import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
TOKEN = os.environ.get('TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID') or os.environ.get('TELEGRAM_CHAT_ID')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')

@app.get('/')
def home():
    return 'SEÑALES PRINCESA DORADA B87 | Servidor activo', 200

@app.post('/webhook')
def webhook():
    if not TOKEN or not CHAT_ID:
        return jsonify(error='Faltan TOKEN o CHAT_ID en Railway'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Se necesita un JSON válido'), 400
    if WEBHOOK_SECRET and data.get('key') != WEBHOOK_SECRET:
        return jsonify(error='No autorizado'), 401

    event = str(data.get('e') or data.get('senal') or data.get('signal') or 'ALERTA')
    side = str(data.get('s') or data.get('direccion') or '')
    symbol = str(data.get('symbol') or data.get('ticker') or data.get('simbolo') or 'XAUUSD')
    tf = str(data.get('tf') or '')
    detail = str(data.get('t') or data.get('text') or data.get('message') or '')
    profile = str(data.get('p') or '')
    price = str(data.get('precio') or '')
    lines = ['👑 SEÑALES PRINCESA DORADA B87', '', f'📊 {symbol}' + (f' | {tf}' if tf else ''), f'🔔 {event}']
    if side:
        lines.append(f'📈 Dirección: {side}')
    if profile:
        lines.append(f'📋 Perfil: {profile}')
    if price:
        lines.append(f'💰 Precio: {price}')
    if detail:
        lines.append(f'📝 {detail}')
    text = '\n'.join(lines)[:4096]
    try:
        r = requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage', json={'chat_id': CHAT_ID, 'text': text}, timeout=10)
        result = r.json()
        if not r.ok or not result.get('ok'):
            return jsonify(error='Telegram rechazó el mensaje', telegram_status=r.status_code), 502
        return jsonify(ok=True, telegram_status=r.status_code), 200
    except (requests.RequestException, ValueError):
        return jsonify(error='Error de comunicación con Telegram'), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8080')))
