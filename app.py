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
    try:
        import openai
        openai.api_key = OPENAI_KEY

        messages = [{"role": "user", "content": msg}]
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        resposta = response.choices[0].message.content
        total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
        print(f"Tokens usados: {total_tokens}")
        return resposta
    except Exception as e:
        print("\n❌ Erro ao acessar ChatGPT:", str(e))
        return None

# Função para enviar mensagem pelo WhatsApp (Z-API)
def send_message_whatsapp(phone, message):
    if not message:
        print("⚠️ Mensagem vazia, não enviada.")
        return

    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": str(phone),
        "message": message
    }
    headers = {
        'Content-Type': 'application/json'
    }

    print("\n📤 Enviando para Z-API:")
    print(f"➡️ URL: {url}")
    print(f"➡️ Payload: {json.dumps(payload, ensure_ascii=False)}")
    print(f"➡️ Headers: {headers}")

    response = requests.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'))
    print("📤 Resposta da Z-API:", response.text)

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    print("\n📥 Endpoint /webhook chamado")
    data = request.json
    print("\n📦 Recebido:", data)

    msg = data.get("text", {}).get("message")
    number = data.get("phone")

    if not msg or not number:
        print("⚠️ Ignorado: sem texto ou número")
        return "Dados inválidos", 400

    resposta = chatgpt_response(msg)
    if resposta:
        send_message_whatsapp(number, resposta)
    else:
        print("⚠️ Nenhuma resposta gerada pela IA — mensagem não enviada")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("\n✅ Flask app inicializado com sucesso")
    app.run(host="0.0.0.0", port=port)