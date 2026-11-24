import os, json, sqlite3, logging, math, hmac
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
import requests
app=Flask(__name__)
logging.basicConfig(level=logging.INFO)
log=logging.getLogger('princesa_dorada')
worker=ThreadPoolExecutor(max_workers=1)
TOKEN=os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID=os.getenv('CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID')
SECRET=os.getenv('WEBHOOK_SECRET','')
DB=os.getenv('DB_PATH',os.path.join(os.getenv('RAILWAY_VOLUME_MOUNT_PATH','.'),'b87_telegram.sqlite3'))
def db():
    c=sqlite3.connect(DB,timeout=15)
    c.execute('CREATE TABLE IF NOT EXISTS trades (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    return c

def telegram(method, **kwargs):
    r=requests.post(f'https://api.telegram.org/bot{TOKEN}/{method}',json={'chat_id':CHAT_ID,**kwargs},timeout=(3,8))
    j=r.json()
    if not j.get('ok'):
        if method=='editMessageText' and 'message is not modified' in j.get('description',''): return {}
        raise RuntimeError('Telegram HTTP '+str(r.status_code))
    return j['result']

def number(v):
    x=float(v)
    if not math.isfinite(x): raise ValueError('invalid number')
    return x

def cohort(d): return (d['symbol'],d['tf'],d['side'],d.get('origin',''))
def rates(c,d):
    past=[json.loads(r[0]) for r in c.execute('SELECT payload FROM trades')]
    past=[x for x in past if x.get('closed') and cohort(x)==cohort(d)]
    n=len(past)
    return n,[round(100*sum(x['hit']>=i for x in past)/n) if n>=30 else None for i in range(1,6)]

def render(d):
    side=d['side']; lines=['👑 PRINCESA DORADA B87','━━━━━━━━━━━━━━━━━━',('🟢 COMPRA' if side=='BUY' else '🔴 VENTA')+' CONFIRMADA',f"{d['symbol']} | TF {d['tf']}",f"Fuerza MTF: {d['force']}% | Calidad: {d['score']}/100",'',f"💰 Entrada: {d['entry']}",f"🛡 SL vigente: {d['sl']}",'','🎯 OBJETIVOS · ACIERTO HISTÓRICO']
    for i,p in enumerate(d['rates'],1):
        lines.append(f"{'✅' if d['hit']>=i else '◻️'} TP{i}: {d['tp'+str(i)]} | "+(f'{p}%' if p is not None else 'En calibración'))
    lines += [f"Muestra: {d['n']} señales cerradas comparables",'Frecuencia histórica, no garantía individual.','━━━━━━━━━━━━━━━━━━',d.get('status','En seguimiento')]
    return '\n'.join(lines)

def process(d):
    try:
        with db() as c:
            tid=d['trade_id']; event=d['event']; row=c.execute('SELECT payload FROM trades WHERE id=?',(tid,)).fetchone()
            old=json.loads(row[0]) if row else None
            if event=='ENTRY':
                if old: return
                sign=1 if d['side']=='BUY' else -1
                e=number(d['entry']); sl=number(d['sl']); targets=[number(d[f'tp{i}']) for i in range(1,6)]
                if sign*(e-sl)<=0 or any(sign*(b-a)<=0 for a,b in zip([e]+targets,targets)): return
                d['n'],d['rates']=rates(c,d); d['hit']=0; d['closed']=False; d['initial_sl']=d['sl']; d['status']='🟡 En seguimiento'
                d['message_id']=telegram('sendMessage',text=render(d))['message_id']
            else:
                if not old or old.get('closed') or int(d['ts'])<int(old['ts']): return
                if d['side']!=old['side']: return
                hit=max(old['hit'],min(5,int(d['hit'])))
                terminal=event in ('STOP','TP5','TIMEOUT','FLIP')
                if event not in ('UPDATE','REVERSAL') and not terminal: return
                sign=1 if old['side']=='BUY' else -1
                protected=sign*(number(d['sl'])-number(old['entry']))>=0
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
