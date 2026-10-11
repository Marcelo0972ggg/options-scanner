from datetime import datetime
import logging
import os
import numpy as np
import pandas as pd
import requests
import yfinance as yf

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)

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


def validar_credenciais_telegram():
  """Valida se o token e chat_id do Telegram estão configurados."""
  token = os.environ.get('TELEGRAM_TOKEN')
  chat_id = os.environ.get('TELEGRAM_CHAT_ID')
  if not token or not chat_id:
    logging.warning('⚠️ Credenciais do Telegram não configuradas no ambiente.')
    return False
  return True


def arredondar_strike_b3(strike):
  """Arredonda o strike para os padrões de negociação da B3 (passos de 0.50)."""
  return round(strike * 2) / 2


def calcular_iv_rank(vol_atual, series_vol):
  """Calcula o IV Rank em uma escala de 0 a 100."""
  min_vol, max_vol = series_vol.min(), series_vol.max()
  if max_vol == min_vol:
    return 50.0
  return round(((vol_atual - min_vol) / (max_vol - min_vol)) * 100.0, 1)


def calcular_rsi(df, periodo=14):
  """Calcula o IFR (RSI) vetorizado."""
  delta = df['Close'].diff()
  gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
  rs = gain / loss
  rsi_series = 100 - (100 / (1 + rs))
  return rsi_series.iloc[-1]


def gerar_ticker_put(ticker_base, strike, data_vencimento):
  """Gera o código da opção PUT no padrão B3 (ex: PETR4M300)."""
  mes = data_vencimento.month
  letra = LETRAS_PUT.get(mes, 'W')
  inteiro = int(np.floor(strike))
  centavos = int(round((strike - inteiro) * 100))
  str_strike = (
      f'{inteiro}' if centavos == 0 else f'{inteiro}{centavos:02d}'
  )
  return f'{ticker_base}{letra}{str_strike}'


def enviar_telegram(mensagem):
  """Envia mensagens formatadas em Markdown via Bot do Telegram."""
  token = os.environ.get('TELEGRAM_TOKEN')
  chat_id = os.environ.get('TELEGRAM_CHAT_ID')

  if not token or not chat_id:
    logging.error('Falha ao enviar Telegram: Credenciais ausentes.')
    return False

  url = f'https://api.telegram.org/bot{token}/sendMessage'
  payload = {'chat_id': chat_id, 'text': mensagem, 'parse_mode': 'Markdown'}

  try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    logging.info('Notificação enviada com sucesso ao Telegram.')
    return True
  except Exception as e:
    logging.error(f'Erro ao enviar mensagem no Telegram: {e}')
    return False
  
