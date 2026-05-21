from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route("/")
def home():
    return "IMPULXOR IA ONLINE"

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    text = f"""
🚨 IMPULXOR IA 🚨

{data.get('ticker')} ORDEN PENDIENTE {data.get('type')}

📍 PRECIO: {data.get('entry')}

🛑 STOPLOSS: {data.get('sl')}

🎯 TP1: {data.get('tp1')}
🎯 TP2: {data.get('tp2')}

⚡ {data.get('risk')}
"""

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    requests.post(url, json=payload)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
