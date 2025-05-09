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
    import openai
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_KEY)

    try:
        messages = [{"role": "user", "content": msg}]
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        resposta = completion.choices[0].message.content
        total_tokens = count_tokens(messages + [{"role": "assistant", "content": resposta}])
        print(f"Tokens usados: {total_tokens}")
        return resposta
    except Exception as e:
        print("\n\n❌ Erro ao acessar ChatGPT:", e, "\n\n")
        return None

# Função para enviar mensagem pelo WhatsApp (Z-API)
def send_message_whatsapp(phone, message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-messages"
    payload = {
        "phone": phone,
        "message": message
    }
    headers = {'Content-Type': 'application/json'}

    print("\n\u2709\ufe0f Enviando para Z-API:")
    print("\u27a1\ufe0f URL:", url)
    print("\u27a1\ufe0f Payload:", json.dumps(payload, ensure_ascii=False))
    print("\u27a1\ufe0f Headers:", headers)

    response = requests.post(url, json=payload, headers=headers)
    print("\n\ud83d\udce4 Resposta da Z-API:", response.text)

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("\n\ud83d\udce6 Endpoint /webhook chamado")
    print("\n\ud83d\udce6 Recebido:", json.dumps(data, indent=4, ensure_ascii=False))

    msg = data.get("text", {}).get("message", "")
    number = data.get("phone", "")
    is_group = data.get("isGroup", False)

    if not msg or not number or is_group:
        print("\n⚠️ Ignorado: sem texto ou número, ou é grupo.")
        return "OK", 200

    print("\n\ud83d\udd0d ENV DEBUG - OPENAI_KEY:", OPENAI_KEY)

    resposta = chatgpt_response(msg)
    if resposta:
        send_message_whatsapp(number, resposta)
    else:
        print("\n⚠️ Nenhuma resposta gerada pela IA — mensagem não enviada")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("\n✅ Flask app inicializado com sucesso")
    app.run(host="0.0.0.0", port=port)
