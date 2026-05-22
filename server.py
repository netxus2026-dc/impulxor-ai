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

signal = data.get("signal", "WAIT")
price = data.get("price", "N/A")
entry_zone = data.get("entry_zone", "N/A")
runner = data.get("runner", "N/A")
risk = data.get("risk", "N/A")

text = f"""
🚨 IMPULXOR IA 🚨

📊 SEÑAL: {signal}

📍 PRECIO: {price}

📦 ZONA: {entry_zone}

🎯 RUNNER: {runner}

⚡ RIESGO: {risk}
"""
