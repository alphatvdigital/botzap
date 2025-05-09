import os
from flask import Flask, request, jsonify
import requests
import json
import tiktoken
from openai import OpenAI

app = Flask(__name__)
print("✅ Flask app inicializado com sucesso")

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

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

# Função compatível com OpenAI SDK >= 1.0
def chatgpt_response(msg):
    print("🔍 ENV DEBUG - OPENAI_KEY:", OPENAI_KEY)

    messages = [{"role": "user", "content": msg}]
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        if response and response.choices and response.choices[0].message.content:
            resposta = str(response.choices[0].message.content).strip()
            total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
            print(f"Tokens usados: {total_tokens}")
            return resposta
        else:
            print("⚠️ Resposta vazia da IA")
            return None

    except Exception as e:
        print("❌ Erro ao acessar ChatGPT:", str(e))
        return None

# Envia mensagem via Z-API
def send_message_whatsapp(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print("📤 Resposta da Z-API:", response.text)

# Webhook principal
@app.route("/webhook", methods=["POST"])
def webhook():
    print("📥 Endpoint /webhook chamado")

    data = request.json
    print("📦 Recebido:", data)

    msg = data.get("text", {}).get("message")
    number = data.get("phone")

    if not msg or not number:
        print("⚠️ Ignorado: sem texto ou número")
        return "OK", 200

    resposta = chatgpt_response(msg)

    # ✅ Valida se resposta não está vazia ou nula
    if resposta and resposta.strip():
        send_message_whatsapp(number, resposta)
    else:
        print("⚠️ Resposta inválida ou vazia — não enviada para o WhatsApp")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
