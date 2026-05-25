from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route("/", methods=["GET"])
def home():
    return "IMPULXOR IA ONLINE"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    signal = data.get("signal", "N/A")
    price = data.get("price", "N/A")
    entry_zone = data.get("entry_zone", "N/A")
    runner = data.get("runner", "N/A")
    risk = data.get("risk", "N/A")
    symbol = data.get("ticker", data.get("symbol", "XAUUSD"))

    text = f"""🚨 IMPULXOR IA 🚨

📊 SÍMBOLO: {symbol}
📌 SEÑAL: {signal}
💰 PRECIO: {price}
🎯 ZONA: {entry_zone}
🏃 RUNNER: {runner}
⚠️ RIESGO: {risk}
"""

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    r = requests.post(url, json=payload, timeout=10)

    return jsonify({
        "ok": True,
        "telegram_status": r.status_code,
        "telegram_response": r.text
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
