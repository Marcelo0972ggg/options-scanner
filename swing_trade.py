# =====================================================================
# SISTEMA OPERACIONAL BLINDADO DE CREDIT PUTS (B3) - v3.0
# Ajustado: Janela de 50 a 21 DTE | Alvo 50% | Stop 25% (Relação 2:1)
# =====================================================================

import logging
import os
import pandas as pd
import yfinance as yf
from datetime import datetime
from utils import enviar_telegram, validar_credenciais_telegram

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Tickers da B3 com boa liquidez para Credit Puts
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

# --- OS 20 CRITÉRIOS DE ENTRADA (VALIDADOS COM VOLUME > 1.5x) ---
CRITERIOS_ENTRADA_ALTA = [
    "1. Martelo clássico em suporte com volume > 1.5x",
    "2. Engolfo de alta expressivo com volume",
    "3. Padrão de Fundo Duplo (W) rompendo pivô",
    "4. Falso Rompimento de Suporte (Spring / Armadilha de Urso)",
    "5. Martelo Invertido com confirmação compradora",
    "6. Harami de Alta (Inside Bar Reversal) com expansão de volume",
    "7. Rompimento de Resistência / Pivô de Alta com volume explosivo",
    "8. Bandeira de Alta (Flag) ativando rompimento",
    "9. Mastro e Flâmula em tendência primária de alta",
    "10. Rompimento de Caixote / Consolidação Lateral com barra elefante",
    "11. Pullback clássico na região da Média Móvel (9 ou 21 períodos)",
    "12. Barra de Reversão de 180 Graus (Fechamento na máxima)",
    "13. Inside Bar rompida a favor do fluxo comprador",
    "14. Três Soldados Brancos consecutivos",
    "15. Confluência de Osciladores (IFR/Estocástico saindo de sobrevenda)",
    "16. Tweaker Bottoms (Fundos Casados) com rejeição de mínima",
    "17. Pin Bar de alta em suporte macroeconômico/médias longas",
    "18. Cup and Handle (Xícara com Alça) rompendo a borda",
    "19. Descanso em Banda de Bollinger inferior com candle de força",
    "20. Aceleração de fluxo comprador no leilão de abertura em zona de suporte"
]

# --- PARÂMETROS DA ESTRATÉGIA (REVISADOS) ---
PARAMETROS_RISCO = {
    "distancia_otm_min": 0.10,      # 10% abaixo do preço spot
    "distancia_otm_max": 0.12,      # 12% abaixo do preço spot
    "largura_strike": 2.00,         # R$ 2,00 fixos entre as pernas
    "alvo_lucro_percentual": 0.50,  # 50% de lucro sobre o prêmio recebido
    "stop_loss_percentual": 0.25,   # 25% de stop loss mecânico (Relação 2:1)
    "dte_max_montagem": 51,         # Até 51 dias para o vencimento na entrada
    "dte_min_saida": 21             # Fechar obrigatoriamente quando atingir 21 dias
}

def escanear_swing_trade():
    """
    Função principal de varredura integrada com os parâmetros e utilitários do Telegram.
    """
    validar_credenciais_telegram()
    logging.info('A escanear oportunidades para Credit Puts...')
    
    for ticker in TICKERS_SWING:
        try:
            dados = yf.download(ticker, period="30d", interval="1d", progress=False)
            if dados.empty:
                continue
                
            preco_atual = float(dados['Close'].iloc[-1])
            volume_atual = float(dados['Volume'].iloc[-1])
            volume_medio = float(dados['Volume'].rolling(window=20).mean().iloc[-1])
            
            if volume_atual >= (volume_medio * 1.5):
                strike_vendido = preco_atual * (1 - PARAMETROS_RISCO["distancia_otm_min"])
                strike_comprado = strike_vendido - PARAMETROS_RISCO["largura_strike"]
                
                mensagem = (
                    f"🚨 *OPORTUNIDADE EM {ticker}* 🚨\n\n"
                    f"• *Spot:* R$ {preco_atual:.2f}\n"
                    f"• *Volume:* Confirmado (> 1.5x da média)\n"
                    f"• *Strike Vendido (Put OTM):* R$ {strike_vendido:.2f}\n"
                    f"• *Strike Comprado (Proteção):* R$ {strike_comprado:.2f}\n"
                    f"• *Metas (2:1):* Alvo 50% | Stop 25%\n"
                    f"• *Ação:* Checar os 20 critérios no gráfico e montar na XP!"
                )
                enviar_telegram(mensagem)
                logging.info(f"Alerta enviado para {ticker}")
                
        except Exception as e:
            logging.error(f"Erro ao processar o ativo {ticker}: {e}")

def auditoria_fechamento_diario(posicoes_abertas):
    """
    Executa a auditoria diária no fechamento para checar Alvos (50%) ou Stops (25%).
    """
    for pos in posicoes_abertas:
        ticker = pos["ticker"]
        premio_inicial = pos["premio_inicial"]
        premio_atual = pos["premio_atual"]
        dte_atual = pos["dte_atual"]
        
        lucro_perc = (premio_inicial - premio_atual) / premio_inicial
        
        if lucro_perc >= PARAMETROS_RISCO["alvo_lucro_percentual"]:
            alerta = f"🎯 *META DE LUCRO ATINGIDA (50%)!* Zerar trava de {ticker} amanhã cedo."
            enviar_telegram(alerta)
        elif lucro_perc <= -PARAMETROS_RISCO["stop_loss_percentual"]:
            alerta = f"🛑 *STOP LOSS ATINGIDO (25%)!* Zerar/rolar trava de {ticker} imediatamente."
            enviar_telegram(alerta)
        elif dte_atual <= PARAMETROS_RISCO["dte_min_saida"]:
            alerta = f"⚠️ *LIMITE DE DTE (21 DIAS)!* Zerar trava de {ticker} para evitar risco de Gamma."
            enviar_telegram(alerta)

if __name__ == "__main__":
    escanear_swing_trade()
  
