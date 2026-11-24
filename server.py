was_protected=sign*(number(old['sl'])-number(old['entry']))>=0
                if event != "REVERSAL" and not terminal and hit==old['hit'] and not (protected and not was_protected): return
                old.update(hit=hit,ts=d['ts'],force=d['force'],score=d['score'],sl=d['sl'],closed=terminal)
                old['status']={'STOP':'🏁 Cierre por stop','TP5':'🏆 Objetivo final cumplido','TIMEOUT':'🏁 Señal vencida','FLIP':'⚠️ Cambio de dirección: señal cerrada','REVERSAL':'⚠️ Reversión detectada por el escáner; seguimiento continúa'}.get(event,'🛡 Protección activa' if protected else '🎯 Objetivo alcanzado')
                telegram('editMessageText',message_id=old['message_id'],text=render(old))
                d=old
            c.execute('INSERT OR REPLACE INTO trades VALUES (?,?)',(tid,json.dumps(d,ensure_ascii=False)))
        log.info('Evento procesado: %s',event)
    except Exception as exc: log.error('Error de procesamiento: %s',type(exc).__name__)

def process_legacy(d):
    event=str(d.get('e') or d.get('event') or '').upper()
    try:
        with db() as c:
            c.execute('CREATE TABLE IF NOT EXISTS legacy_seen (id TEXT PRIMARY KEY, ts REAL)')
            import time, hashlib
            now=time.time()
            c.execute('DELETE FROM legacy_seen WHERE ts < ?', (now-86400,))
            symbol=str(d.get('symbol') or d.get('ticker') or 'Activo no indicado')
            tf=str(d.get('tf') or '')
            side=str(d.get('s') or d.get('side') or '')
            detail=str(d.get('t') or d.get('text') or d.get('message') or '')
            key=str(d.get('event_id') or hashlib.sha256(json.dumps([event,symbol,tf,side,detail],ensure_ascii=False).encode()).hexdigest())
            if c.execute('SELECT 1 FROM legacy_seen WHERE id=?',(key,)).fetchone(): return
            lines=['👑 SEÑALES PRINCESA DORADA','━━━━━━━━━━━━━━━━━━',f'{symbol} | {tf}',event,side]
            for k,label in [('entry','Entrada'),('sl','SL')]+[(f'tp{i}',f'TP{i}') for i in range(1,6)]:
                if d.get(k) not in (None,'','na','NaN'): lines.append(f'{label}: {d[k]}')
            if detail: lines.append(detail.replace('IMPULXOR','PRINCESA DORADA'))
            telegram('sendMessage',text='\n'.join(lines)[:4096])
            c.execute('INSERT INTO legacy_seen VALUES (?,?)',(key,now))
        log.info('Alerta compatible entregada: %s',event)
    except Exception as exc: log.error('Error Telegram formato anterior: %s',type(exc).__name__)

@app.get('/')
def home(): return 'PRINCESA DORADA B87 | Servidor activo',200
@app.post('/webhook')
def webhook():
    if not TOKEN or not CHAT_ID: return jsonify(error='Faltan variables'),503
    d=request.get_json(silent=True)
    if not isinstance(d,dict): return jsonify(error='JSON inválido'),400
    if SECRET and not hmac.compare_digest(str(d.get('token') or d.get('key') or ''),SECRET): return jsonify(error='No autorizado'),401
    if not d.get('trade_id'):
        event=str(d.get('e') or d.get('event') or '').upper()
        if not event or any(x in event for x in ('WATCH','PREPARE','PRE_')):
            log.info('Alerta de vigilancia omitida: %s',event)
            return jsonify(status='ignored_watch'),200
        worker.submit(process_legacy,d)
        return jsonify(status='accepted_legacy'),202
    if d.get('event') not in ('ENTRY','UPDATE','REVERSAL','STOP','TP5','TIMEOUT','FLIP'): return jsonify(status='ignored_event'),200
    try:
        for k in ('trade_id','symbol','tf','side','event','ts','score','force','entry','sl','hit'): d[k]
        if d['side'] not in ('BUY','SELL'): raise ValueError()
        int(d['ts']); int(d['hit']); number(d['sl']); number(d['entry']); number(d['score']); number(d['force'])
        if d['event']=='ENTRY':
            for i in range(1,6): number(d[f'tp{i}'])
    except (KeyError,ValueError,TypeError): return jsonify(error='Campos inválidos'),400
    worker.submit(process,d)
    return jsonify(status='accepted'),202
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))
