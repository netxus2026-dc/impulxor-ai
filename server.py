sign=1 if old['side']=='BUY' else -1
                protected=sign*(number(d['sl'])-number(old['entry']))>=0
                was_protected=sign*(number(old['sl'])-number(old['entry']))>=0
                if event != "REVERSAL" and not terminal and hit==old['hit'] and not (protected and (not was_protected or sign*(number(d['sl'])-number(old['sl']))>0)): return
                old.update(hit=hit,ts=d['ts'],force=d['force'],score=d['score'],sl=d['sl'],closed=terminal)
                old['status']={'STOP':'🏁 Cierre por stop','TP5':'🏆 Objetivo final cumplido','TIMEOUT':'🏁 Señal vencida','FLIP':'⚠️ Cambio de dirección: señal cerrada','REVERSAL':'⚠️ Invalidación detectada por el escáner; seguimiento continúa'}.get(event,'🛡 Protección activa' if protected else '🎯 Objetivo alcanzado')
                telegram('editMessageText',message_id=old['message_id'],text=render(old))
                d=old
            c.execute('INSERT OR REPLACE INTO trades VALUES (?,?)',(tid,json.dumps(d,ensure_ascii=False)))
        log.info('Evento procesado: %s',event)
    except Exception as exc: log.error('Error de procesamiento: %s',type(exc).__name__)

@app.get('/')
def home(): return 'PRINCESA DORADA B88 | Servidor activo',200
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
        log.info('Formato antiguo omitido: %s',event)
        return jsonify(status='ignored_legacy'),200
    if d.get('event') not in ('ENTRY','UPDATE','REVERSAL','STOP','TP5','TIMEOUT','FLIP'): return jsonify(status='ignored_event'),200
    try:
        for k in ('trade_id','symbol','tf','side','event','ts','score','force','entry','sl','hit'): d[k]
        if d['side'] not in ('BUY','SELL'): raise ValueError()
        int(d['ts']); int(d['hit']); number(d['sl']); number(d['entry'])
        for k in ('score','force'):
            if d[k] is not None and d[k] != 'N/D': number(d[k])
            else: d[k]='N/D'
        if d['event']=='ENTRY':
            targets=[number(d[f'tp{i}']) for i in range(1,6)]
            sign=1 if d['side']=='BUY' else -1
            e=number(d['entry']); sl=number(d['sl'])
            if sign*(e-sl)<=0 or any(sign*(b-a)<=0 for a,b in zip([e]+targets,targets)):
                log.warning('ENTRY rechazada: niveles inválidos')
                return jsonify(error='Niveles SL/TP inválidos'),400
    except (KeyError,ValueError,TypeError) as exc:
        log.warning('Webhook rechazado: %s',type(exc).__name__)
        return jsonify(error='Campos inválidos'),400
    worker.submit(process,d)
    return jsonify(status='accepted'),202
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))
