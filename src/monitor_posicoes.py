from datetime import datetime
import logging
import os
import yfinance as yf
from utils import enviar_telegram, validar_credenciais_telegram

POSICOES_ATIVAS = [
    {
        'ticker': 'PETR4.SA',
        'credito_inicial': 0.85,
        'strike_v': 38.0,
        'vencimento': '2026-11-20',
    },
    {
        'ticker': 'VALE3.SA',
        'credito_inicial': 1.10,
        'strike_v': 62.0,
        'vencimento': '2026-11-20',
    },
]


def monitorar_carteira():
  validar_credenciais_telegram()
  logging.info('A verificar posições abertas...')
  alertas = []

  hoje = datetime.now()

  for pos in POSICOES_ATIVAS:
    try:
      ticker = pos['ticker']
      ativo = yf.Ticker(ticker)
      df = ativo.history(period='5d')
      if df.empty:
        continue

      preco_atual = df['Close'].iloc[-1]
      vencimento_dt = datetime.strptime(pos['vencimento'], '%Y-%m-%d')
      dte = (vencimento_dt - hoje).days

      alerta_dte = dte <= 21
      distancia_strike = ((preco_atual - pos['strike_v']) / preco_atual) * 100

      if alerta_dte or distancia_strike < 4.0:
        acao_sugerida = (
            'Encerrar por DTE (21 dias)'
            if alerta_dte
            else 'Monitorar proximidade do strike!'
        )
        msg_alerta = (
            f'⚠️ *Atenção à Posição: {ticker.replace(".SA", "")}*\n'
            f'• Preço Atual: R$ {preco_atual:.2f} | Strike Venda: R$'
            f' {pos["strike_v"]:.2f}\n'
            f'• Dias para Vencimento (DTE): *{dte} dias*\n'
            f'• Distância do Strike: {distancia_strike:.1f}%\n'
            f'💡 *Ação Sugerida*: {acao_sugerida}\n'
        )
        alertas.append(msg_alerta)
    except Exception as e:
      logging.error(f'Erro ao monitorar {pos["ticker"]}: {e}')

  if alertas:
    msg = '📊 *Monitor de Gestão de Posições*:\n\n' + '\n'.join(alertas)
    enviar_telegram(msg)
  else:
    logging.info('Nenhum alerta crítico nas posições ativas.')


if __name__ == '__main__':
  monitorar_carteira()
    
