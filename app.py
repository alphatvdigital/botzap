import os
from flask import Flask, request, jsonify
import requests
import json
import tiktoken

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
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }
    messages = [{"role": "user", "content": msg}]
    body = {
        "model": "gpt-3.5-turbo",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=body)
    data = response.json()

    if "choices" not in data:
        print("Erro na resposta do ChatGPT:", data)
        return "Desculpe, ocorreu um erro ao processar sua mensagem."

    resposta = data['choices'][0]['message']['content']
    total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
    print(f"Tokens usados: {total_tokens}")
    return resposta

# Função para enviar mensagem pelo WhatsApp (Z-API)
def send_message_whatsapp(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print("Resposta da Z-API:", response.text)

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Recebido:", data)

    msg = data.get("text", {}).get("message", "")
    number = data.get("phone", "")

    if not msg or not number:
        return "Dados inválidos", 400

    resposta = chatgpt_response(msg)
    send_message_whatsapp(number, resposta)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)