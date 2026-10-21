import os
import json
import requests
from flask import Flask, request
import google.generativeai as genai
from PIL import Image
import io

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def receber_mensagem():
    dados = request.get_json()
    
    if "message" in dados and "photo" in dados["message"]:
        chat_id = dados["message"]["chat"]["id"]
        
        fotos = dados["message"]["photo"]
        file_id = fotos[-1]["file_id"]
        
        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
        resposta_info = requests.get(file_info_url).json()
        file_path = resposta_info["result"]["file_path"]
        
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        imagem_bytes = requests.get(download_url).content
        
        img = Image.open(io.BytesIO(imagem_bytes))
        
        prompt = """
        Analise esta imagem de nota de corretagem ou boleta de opções (Trava de Alta com Put ou PCS).
        Extraia rigorosamente os seguintes dados em formato JSON puro (sem markdown):
        {
          "ticker": "ex: BOVA11.SA",
          "tipo": "PCS",
          "strike_vendido": 0.0,
          "premio_recebido": 0.0,
          "vencimento": "AAAA-MM-DD"
        }
        """
        
        resposta_ia = model.generate_content([prompt, img])
        texto_resposta = resposta_ia.text.replace("```json", "").replace("```", "").strip()
        
        try:
            nova_posicao = json.loads(texto_resposta)
            
            msg = f"✅ <b>Posição Detetada e Registada!</b>\n" \
                  f"Ativo: {nova_posicao.get('ticker')}\n" \
                  f"Strike: R$ {nova_posicao.get('strike_vendido')}\n" \
                  f"Prêmio: R$ {nova_posicao.get('premio_recebido')}\n" \
                  f"Vencimento: {nova_posicao.get('vencimento')}"
            
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
            
        except Exception as e:
            err_msg = f"⚠️ Não consegui interpretar os dados da imagem. Certifique-se de que os valores estão legíveis."
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": err_msg})

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
  
