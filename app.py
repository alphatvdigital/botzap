import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import tiktoken

app = Flask(__name__)

ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")

ADMINS = ["5585991845383"]
BOT_ATIVO = True  # Ativado por padrão

# Contagem de tokens para rastrear custo
def count_tokens(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = 0
    for message in messages:
        total_tokens += 4  # cada mensagem tem 4 tokens extras
        for key, value in message.items():
            total_tokens += len(encoding.encode(value))
    total_tokens += 2  # fim da conversa
    return total_tokens

# Chamada ao ChatGPT
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
        print("❌ Erro na resposta do ChatGPT:", data)
        return "Desculpe, houve um erro ao tentar responder."

    resposta = data["choices"][0]["message"]["content"]
    total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
    print(f"📊 Tokens usados: {total_tokens}")
    return resposta

# Envia mensagem pela Z-API
def send_message_whatsapp(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    payload = {"phone": phone, "message": message}
    headers = {
        'Content-Type': 'application/json',
        'Client-Token': ZAPI_CLIENT_TOKEN
    }
    print(f"\n[Z-API] Enviando para {phone}: {message}")
    response = requests.post(url, headers=headers, json=payload)
    print("[Z-API] Resposta:", response.text)

# Webhook principal
@app.route("/webhook", methods=["POST"])
def webhook():
    global BOT_ATIVO

    data = request.json
    print("\n📥 Endpoint /webhook chamado")
    print("📦 Recebido:", json.dumps(data, indent=4))

    is_group = data.get("isGroup", False)
    msg = data.get("text", {}).get("message", "")
    number = data.get("phone", "")

    # Ignora grupos
    if is_group or not msg or not number:
        print("⚠️ Ignorado: grupo ou mensagem vazia.")
        return "OK", 200

    # Apenas administradores podem ativar/desativar o bot
    if number in ADMINS:
        comando = msg.strip().lower()
        if comando == "bot off":
            BOT_ATIVO = False
            send_message_whatsapp(number, "🤖 Bot desativado com sucesso.")
            print("❌ Bot foi desativado.")
            return "OK", 200
        elif comando == "bot on":
            BOT_ATIVO = True
            send_message_whatsapp(number, "✅ Bot ativado com sucesso.")
            print("✅ Bot foi ativado.")
            return "OK", 200

    # Verifica se o bot está ativo
    if not BOT_ATIVO:
        print("⛔ Bot está desativado.")
        return "OK", 200

    # Horário permitido (9h–22h)
    hora_atual = datetime.now().hour
    if hora_atual < 9 or hora_atual >= 22:
        print("⏰ Fora do horário de atendimento. Ignorando.")
        return "OK", 200

    resposta = chatgpt_response(msg)
    send_message_whatsapp(number, resposta)
    return "OK", 200

# Inicializa o servidor Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("✅ Flask app inicializado com sucesso")
    app.run(host="0.0.0.0", port=port)
