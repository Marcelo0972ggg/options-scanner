import logging
import os
from utils import enviar_telegram, validar_credenciais_telegram


def calcular_dimensionamento():
  validar_credenciais_telegram()

  # Parâmetros da sua banca / conta de opções
  capital_total = 50000.0  # Exemplo: R$ 50.000,00 alocados para renda/opções
  risco_max_portfolio_pct = (
      2.0  # Risco máximo de perda total aceitável por operação (% da banca)
  )

  # Exemplo de uma trava específica encontrada pelo robô:
  # Risco por trava = (Diferença dos strikes - Crédito recebido) * quantidade de lotes
  largura_trava = 3.00  # Ex: Strike vendido 40, comprado 37
  credito_recebido = 0.80  # Ex: R$ 0.80 por opção
  risco_unitario_lote = (largura_trava - credito_recebido) * 100  # por 100 ações

  capital_risco_permitido = capital_total * (risco_max_portfolio_pct / 100.0)
  quantidade_max_lotes = int(capital_risco_permitido / risco_unitario_lote)

  msg = (
      '🛡️ *Relatório de Dimensionamento de Risco*:\n\n'
      f'• Capital Base: R$ {capital_total:,.2f}\n'
      f'• Risco Máximo Alvo: {risco_max_portfolio_pct}% (R$'
      f' {capital_risco_permitido:,.2f})\n\n'
      f'• *Sugestão para a Trava (Largura R$ {largura_trava:.2f} | Crédito R$'
      f' {credito_recebido:.2f}):*\n'
      f'  Risco por Lote (100 opções): R$ {risco_unitario_lote:,.2f}\n'
      f'  📦 *Quantidade Máxima Recomendada*: *{quantidade_max_lotes} lotes*'
      ' (opções)\n\n'
      '⚠️ Nunca ultrapasse o limite de exposição ao risco calculado para proteger'
      ' o seu capital a longo prazo.'
  )

  enviar_telegram(msg)


if __name__ == '__main__':
  calcular_dimensionamento()
  
