from datetime import datetime, timedelta
import os
import warnings
import numpy as np
import pandas as pd
import requests
import yfinance as yf

warnings.filterwarnings('ignore')

TICKERS_ACOES = [
    'PETR4.SA',
    'VALE3.SA',
    'BOVA11.SA',
    'BBDC4.SA',
    'BBAS3.SA',
    'ITSA4.SA',
    'WEGE3.SA',
    'PRIO3.SA',
    'ABEV3.SA',
    'RENT3.SA',
    'AXIA3.SA',
    'SUZB3.SA',
    'GGBR4.SA',
    'CSAN3.SA',
]

LETRAS_PUT = {
    1: 'M',
    2: 'N',
    3: 'O',
    4: 'P',
    5: 'Q',
    6: 'R',
    7: 'S',
    8: 'T',
    9: 'U',
    10: 'V',
    11: 'W',
    12: 'X',
}


def arredondar_strike_b3(strike):
  return round(strike * 2) / 2


def checar_tendencia_flexivel(df):
  """Tendência equilibrada: Permite maior agilidade sem perder o alinhamento."""
  if len(df) < 30:
    return False
  df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
  df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
  p, e9, e21 = df['Close'].iloc[-1], df['EMA9'].iloc[-1], df['EMA21'].iloc[-1]
  return p > e21 or e9 >= e21


def calcular_iv_rank(vol_atual, series_vol):
  min_vol, max_vol = series_vol.min(), series_vol.max()
  if max_vol == min_vol:
    return 50.0
  return round(((vol_atual - min_vol) / (max_vol - min_vol)) * 100.0, 1)


def gerar_ticker_put(ticker_base, strike, data_vencimento):
  mes = data_vencimento.month
  letra = LETRAS_PUT.get(mes, 'W')
  inteiro = int(np.floor(strike))
  centavos = int(round((strike - inteiro) * 100))
  str_strike = (
      f'{inteiro}' if centavos == 0 else f'{inteiro}{centavos:02d}'
  )
  return f'{ticker_base}{letra}{str_strike}'


def enviar_telegram(mensagem):
  token = os.environ.get('TELEGRAM_TOKEN')
  chat_id = os.environ.get('TELEGRAM_CHAT_ID')
  if not token or not chat_id:
    return
  url = f'https://api.telegram.org/bot{token}/sendMessage'
  payload = {'chat_id': chat_id, 'text': mensagem, 'parse_mode': 'Markdown'}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception:
    pass


def escanear_travas_put_4560():
  hoje = datetime.now()
  vencimento_ref = hoje + timedelta(days=55)  # Janela de 45 a 60 DTE
  resultados = []

  for ticker_symbol in TICKERS_ACOES:
    try:
      ativo = yf.Ticker(ticker_symbol)
      df_d = ativo.history(period='1y', interval='1d')
      if df_d.empty or len(df_d) < 40:
        continue

      # Tendência flexibilizada para maior assertividade e agilidade
      tendencia_ok = checar_tendencia_flexivel(df_d)

      # IFR (14) Diário
      delta_p = df_d['Close'].diff()
      gain = (delta_p.where(delta_p > 0, 0)).rolling(14).mean()
      loss = (-delta_p.where(delta_p < 0, 0)).rolling(14).mean()
      rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]

      # Filtro de Pullback (Volume controlado)
      vol_hoje = df_d['Volume'].iloc[-1]
      vol_media20 = df_d['Volume'].tail(20).mean()
      pullback_aceitavel = vol_hoje <= (vol_media20 * 1.30)

      # Volatilidade e IV Rank
      returns = np.log(df_d['Close'] / df_d['Close'].shift(1))
      vol_roll = returns.rolling(window=21).std() * np.sqrt(252) * 100
      vol_atual = vol_roll.iloc[-1]
      iv_rank = calcular_iv_rank(vol_atual, vol_roll.dropna())

      # Preço Spot e Afastamento (Corredor seguro e ousado: 7.5% a 11.5%)
      preco = df_d['Close'].iloc[-1]
      suporte_20d = df_d['Low'].tail(20).min()
      strike_v_calc = min(suporte_20d, preco * 0.91)
      strike_v = arredondar_strike_b3(strike_v_calc)

      largura = 3.00 if preco >= 35.0 else 2.00
      strike_c = strike_v - largura
      distancia_pct = ((preco - strike_v) / preco) * 100.0

      if not (7.0 <= distancia_pct <= 12.0):
        continue

      credito_est = round(largura * 0.26, 2)

      # Sistema de Pontuação Balanceado (Ousadia + Segurança)
      score = 0
      if tendencia_ok:
        score += 35
      if pullback_aceitavel:
        score += 25
      if 38.0 <= rsi <= 70.0:
        score += 25
      if iv_rank >= 15.0:
        score += 15

      # Limiar ajustado para não deixar passar boas oportunidades
      if score >= 60:
        status = '🟢 EXCELENTE (Oportunidade Ativa)'
      elif score >= 45:
        status = '🟡 BOM (Monitorar / Mão Moderada)'
      else:
        status = '🔴 DESCARTE'

      raiz = ticker_symbol.replace('.SA', '')
      put_v = gerar_ticker_put(raiz, strike_v, vencimento_ref)
      put_c = gerar_ticker_put(raiz, strike_c, vencimento_ref)

      if status != '🔴 DESCARTE':
        resultados.append({
            'Ativo': raiz,
            'Preço': round(preco, 2),
            'Trava': f'{put_v} / {put_c}',
            'Strikes': f'R${strike_v:.2f} / R${strike_c:.2f}',
            'Distância': f'{distancia_pct:.1f}%',
            'Crédito Est.': f'R$ {credito_est:.2f}',
            'Status': status,
        })
    except Exception:
      continue

  if resultados:
    msg = '🛡️ *Radar Travas de Put (45-60 DTE)*:\n\n'
    for r in resultados:
      msg += (
          f"• *{r['Ativo']}* | Preço: R$ {r['Preço']} | Distância:"
          f" {r['Distância']}\n"
      )
      msg += f"  Trava: `{r['Trava']}` ({r['Strikes']})\n"
      msg += (
          f"  Crédito Est.: {r['Crédito Est.']} | Avaliação: {r['Status']}\n\n"
      )

    # Lembrete estratégico de Gestão, Rolagem e Reciclagem de Capital
    msg += (
        '💡 *Dica de Gestão & Ciclo*:\n'
        '• Verifique suas posições abertas: se alguma atingiu *65% a 75% de'
        ' lucro* ou chegou a *21 DTE*, encerre o trade!\n'
        '• Se o mesmo ativo aparecer novamente com critérios limpos, é seguro'
        ' zerar o lucro e montar uma nova trava para reiniciar o ciclo.'
    )

    enviar_telegram(msg)


if __name__ == '__main__':
  escanear_travas_put_4560()
