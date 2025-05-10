import os
from flask import Flask, request, jsonify
import requests
import json
import tiktoken
import openai

app = Flask(__name__)

# Variáveis de ambiente para Z-API e OpenAI
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")               # ID da instância
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")                     # Token da instância (URL)
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")       # Token de Segurança (Client-Token)
OPENAI_KEY = os.getenv("OPENAI_KEY")                     # Chave da OpenAI

# Configura cliente OpenAI
openai.api_key = OPENAI_KEY

# Contador de tokens usado (opcional)
def count_tokens(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = 0
    for message in messages:
        total_tokens += 4
        for key, value in message.items():
            total_tokens += len(encoding.encode(value))
    total_tokens += 2
    return total_tokens

# Gera resposta via ChatGPT
def chatgpt_response(msg):
    messages = [{"role": "user", "content": msg}]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        resposta = response.choices[0].message.content.strip()
        total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
        print(f"[TOKENS] Tokens usados: {total_tokens}")
        return resposta
    except Exception as e:
        print(f"[ERRO] Erro ao acessar ChatGPT: {e}")
        return None

# Envia mensagem via Z-API
# Inclui Client-Token no header conforme requisitado
def send_message_whatsapp(phone, message):
    if not phone or not message:
        print("[ERRO] Número ou mensagem vazios. Nada será enviado.")
        return
    if "-group" in phone:
        print("[INFO] Ignorado: mensagem de grupo não suportada.")
        return

    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {"phone": phone, "message": message}
    headers = {
        'Content-Type': 'application/json',
        'Client-Token': ZAPI_CLIENT_TOKEN
    }

    print("[Z-API] Enviando mensagem:")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, ensure_ascii=False)}")
    print(f"  Headers: {{'Content-Type': 'application/json', 'Client-Token': '<oculto>'}}")

    response = requests.post(url, json=payload, headers=headers)
    print(f"[Z-API] Resposta: {response.text}")

# Rota webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    print("[Webhook] Endpoint /webhook chamado")
    data = request.json
    print(f"[Webhook] Recebido: {json.dumps(data, indent=4, ensure_ascii=False)}")

    msg = data.get("text", {}).get("message", "")
    number = data.get("phone", "")
    is_group = data.get("isGroup", False)

    # Ignora mensagens de grupo e vazias
    if not msg or not number or is_group:
        print("[INFO] Ignorado: sem texto, número vazio ou grupo.")
        return "OK", 200

    resposta = chatgpt_response(msg)
    if resposta:
        send_message_whatsapp(number, resposta)
    else:
        print("[INFO] Nenhuma resposta gerada pela IA — mensagem não enviada")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("[INFO] Inicializando app Flask...")
    app.run(host="0.0.0.0", port=port)
