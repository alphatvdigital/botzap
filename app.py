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
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": msg}]
        )
        resposta = response.choices[0].message.content.strip()
        return resposta
    except Exception as e:
        print("❌ Erro ao acessar ChatGPT:", e)
        return None

# Função para enviar mensagem pelo WhatsApp (Z-API)
def send_message_whatsapp(phone, message):
    if not phone or not message:
        print("❌ Erro: número ou mensagem está vazia. Nada será enviado.")
        return

    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {'Content-Type': 'application/json'}

    print(f"\n📤 Enviando para Z-API:")
    print(f"➡️ URL: {url}")
    print(f"➡️ Payload: {json.dumps(payload)}")
    print(f"➡️ Headers: {headers}\n")

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"📤 Resposta da Z-API: {response.text}")

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    print("\n📥 Endpoint /webhook chamado")
    data = request.json
    print("\n📦 Recebido:", json.dumps(data, indent=4, ensure_ascii=False))

    msg = data.get("text", {}).get("message", "")
    number = data.get("phone", "")

    if not msg or not number or "-group" in number:
        print("⚠️ Ignorado: sem texto ou número, ou é grupo.")
        return "Dados inválidos", 400

    print("\n🔍 ENV DEBUG - OPENAI_KEY:", OPENAI_KEY)
    resposta = chatgpt_response(msg)

    if resposta:
        send_message_whatsapp(number, resposta)
    else:
        print("⚠️ Nenhuma resposta gerada pela IA — mensagem não enviada")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask app inicializado com sucesso")
    app.run(host="0.0.0.0", port=port)