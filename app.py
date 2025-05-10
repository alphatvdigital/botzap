import os
from flask import Flask, request, jsonify
import requests
import json
import tiktoken
import openai

app = Flask(__name__)

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Função para contar tokens usados
def count_tokens(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = 0
    for message in messages:
        total_tokens += 4
        for key, value in message.items():
            total_tokens += len(encoding.encode(value))
    total_tokens += 2
    return total_tokens

# Função para enviar resposta do ChatGPT
def chatgpt_response(msg):
    openai.api_key = OPENAI_KEY

    messages = [{"role": "user", "content": msg}]
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        resposta = response.choices[0].message.content
        total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
        print(f"[TOKENS] Tokens usados: {total_tokens}")
        return resposta
    except Exception as e:
        print(f"[ERRO] Erro ao acessar ChatGPT: {e}\n")
        return None

# Função para enviar mensagem pelo WhatsApp (Z-API)
def send_message_whatsapp(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {'Content-Type': 'application/json'}

    print("[Z-API] Enviando para Z-API:")
    print(f"[Z-API] URL: {url}")
    print(f"[Z-API] Payload: {json.dumps(payload)}")

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"[Z-API] Resposta: {response.text}")

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    print("\n[Webhook] Endpoint /webhook chamado")
    data = request.json
    print(f"[Webhook] Recebido: {json.dumps(data, indent=4)}")

    msg = data.get("text", {}).get("message", "")
    number = data.get("phone", "")
    is_group = data.get("isGroup", False)

    if not msg or not number or is_group:
        print("[INFO] Ignorado: sem texto ou número, ou é grupo.")
        return "Ignorado", 200

    print(f"[DEBUG] OPENAI_KEY: {OPENAI_KEY[:8]}...")

    resposta = chatgpt_response(msg)
    if resposta:
        send_message_whatsapp(number, resposta)
    else:
        print("[INFO] Nenhuma resposta gerada pela IA — mensagem não enviada")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("\n[INFO] Inicializando app Flask...")
    app.run(host="0.0.0.0", port=port)
