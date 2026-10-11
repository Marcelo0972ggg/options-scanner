import logging
import os
import pandas as pd
import yfinance as yf
from utils import enviar_telegram, validar_credenciais_telegram

# Tickers da B3 com boa liquidez para Swing Trade
TICKERS_SWING = [
    'PETR4.SA',
    'VALE3.SA',
    'BBAS3.SA',
    'BBDC4.SA',
    'ITSA4.SA',
    'WEGE3.SA',
    'PRIO3.SA',
    'ABEV3.SA',
    'RENT3.SA',
    'SUZB3.SA',
    'GGBR4.SA',
    'EQTL3.SA',
]


def escanear_swing_trade():
  validar_credenciais_telegram()
  logging.info('A escanear oportunidades de Swing Trade (FR2 / Média)...')
  oportunidades = []

  for ticker in TICKERS_SWING:
    try:
      df = yf.Ticker(ticker).history(period='1y')
      if len(df) < 200:
        continue

      # Média Móvel Simples de 200 e Média Exponencial de 9
      df['MMA200'] = df['Close'].rolling(window=200).mean()
      df['MME9'] = df['Close'].ewm(span=9, adjust=False).mean()

      preco_atual = df['Close'].iloc[-1]
      mma200 = df['MMA200'].iloc[-1]

      # Regra 1: Tendência principal de alta (Preço acima da MM200)
      if preco_atual > mma200:
        fecho_hoje = df['Close'].iloc[-1]
        fecho_ontem = df['Close'].iloc[-2]
        fecho_antes = df['Close'].iloc[-3]

        # Regra 2: Fecho de Relação (2 dias seguidos de queda dentro da tendência de alta)
        if fecho_hoje < fecho_ontem and fecho_ontem < fecho_antes:
          maxima_2dias = max(df['High'].iloc[-2], df['High'].iloc[-1])
          oportunidades.append({
              'ticker': ticker.replace('.SA', ''),
              'preco': round(preco_atual, 2),
              'alvo_maxima': round(maxima_2dias, 2),
          })
    except Exception as e:
      logging.error(f'Erro ao analisar {ticker}: {e}')

  if oportunidades:
    msg = '📈 *Radar de Swing Trade (Regressão à Média / FR2)*:\n\n'
    for op in oportunidades:
      msg += (
          f"• *{op['ticker']}* | Preço: R$ {op['preco']:.2f}\n  👉 *Alvo"
          f" (Máxima 2D)*: R$ {op['alvo_maxima']:.2f}\n"
      )
    msg += '\n💡 *Estratégia*: Compra na correção de tendência de alta com foco em repique de curto prazo.'
    enviar_telegram(msg)
  else:
    logging.info('Nenhuma oportunidade de Swing Trade encontrada hoje.')


if __name__ == '__main__':
  escanear_swing_trade()
  
