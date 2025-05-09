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

openai.api_key = OPENAI_KEY  # Usar o novo padrão da lib openai>=1.0.0

# Função para contar tokens
def count_tokens(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = 0
    for message in messages:
        total_tokens += 4
        for key, value in message.items():
            total_tokens += len(encoding.encode(value))
    total_tokens += 2
    return total_tokens

# Função para resposta do ChatGPT
def chatgpt_response(msg):
    try:
        messages = [{"role": "user", "content": msg}]
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        total_tokens = count_tokens(messages + [{"role": "assistant", "content": reply}])
        print(f"Tokens usados: {total_tokens}")
        return reply
    except Exception as e:
        print("❌ Erro ao acessar ChatGPT:", e)
        return None

# Função para enviar mensagem via Z-API
def send_message_whatsapp(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {'Content-Type': 'application/json'}

    print("\n📤 Enviando para Z-API:")
    print(f"➡️ URL: {url}")
    print(f"➡️ Payload: {json.dumps(payload)}")
    print(f"➡️ Headers: {headers}")

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta da Z-API:", response.text)

# Webhook principal
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("\n📥 Endpoint /webhook chamado")
    print("📦 Recebido:", data)

    msg = data.get("text", {}).get("message")
    number = data.get("phone")

    if not msg or not number:
        print("⚠️ Ignorado: sem texto ou número")
        return "Dados inválidos", 400

    resposta = chatgpt_response(msg)
    if not resposta:
        print("⚠️ Nenhuma resposta gerada pela IA — mensagem não enviada")
        return "Erro ao gerar resposta", 200

    send_message_whatsapp(number, resposta)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask app inicializado com sucesso")
    app.run(host="0.0.0.0", port=port)