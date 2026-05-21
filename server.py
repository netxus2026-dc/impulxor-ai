from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "TU_TOKEN_TELEGRAM"
CHAT_ID = "TU_CHAT_ID"

@app.route("/", methods=["GET"])
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

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
