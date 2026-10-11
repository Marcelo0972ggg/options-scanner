import logging
import os
import numpy as np
import pandas as pd
import yfinance as yf
from utils import (
    calcular_iv_rank_historico,
    enviar_telegram,
    validar_credenciais_telegram,
)

TICKERS_UNIVERSO = [
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
    'SMAL11.SA',
]


def escanear_iv_rank():
  validar_credenciais_telegram()
  logging.info('Calculando IV Rank do universo de ativos...')
  oportunidades = []

  for ticker in TICKERS_UNIVERSO:
    try:
      df = yf.Ticker(ticker).history(period='1y')
      if len(df) < 100:
        continue

      iv_rank = calcular_iv_rank_historico(df)
      preco = df['Close'].iloc[-1]

      # IV Rank acima de 50 indica opções caras (excelente para vender)
      if iv_rank >= 50.0:
        oportunidades.append({
            'ticker': ticker.replace('.SA', ''),
            'iv_rank': iv_rank,
            'preco': round(preco, 2),
        })
    except Exception as e:
      logging.error(f'Erro no IV Rank para {ticker}: {e}')

  if oportunidades:
    # Ordena pelos maiores IV Ranks
    oportunidades = sorted(
        oportunidades, key=lambda x: x['iv_rank'], reverse=True
    )

    msg = '🔥 *Radar de Volatilidade Implícita (IV Rank Alto)*:\n\n'
    for o in oportunidades:
      msg += (
          f"• *{o['ticker']}* | Preço: R$ {o['preco']} | IV Rank:"
          f" *{o['iv_rank']:.1f}%*\n"
      )

    msg += '\n💡 *Dica*: Ativos com IV Rank > 50 estão com opções historicamente caras. Cenário ideal para Travas de Crédito e Vendas Cobertas!'
    enviar_telegram(msg)


if __name__ == '__main__':
  escanear_iv_rank()
