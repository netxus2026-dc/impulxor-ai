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
🔥 IMPULXOR ALERTA

SYMBOL: {data.get('ticker')}
SIGNAL: {data.get('signal')}
PRICE: {data.get('price')}
TF: {data.get('tf')}
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
