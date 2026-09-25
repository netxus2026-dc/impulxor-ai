# IMPULXOR V73 — Cambios respecto a V72

Archivo: `IMPULXOR_V73.pine` (Pine Script v6). Auditoría estática aplicada; el
script debe compilarse en TradingView para validación final, porque el
compilador de Pine no existe fuera de la plataforma.

## Correcciones de lógica operativa

1. **El CORE (`masterDir`) vuelve a poder cambiar.**
   En V72 la reversa exigía estructura + displacement + barrida en la misma vela
   y dos velas consecutivas. En la práctica la dirección quedaba pegada para
   siempre y nunca volvía a NEUTRO. Ahora:
   - La barrida vale si ocurrió en las últimas `reverseRaidBars` velas (input, 6).
   - Las confirmaciones se cuentan dentro de `reverseWindowBars` velas (input, 10),
     no consecutivas.
   - Si el CORE pierde ventaja de score y continuación durante
     `neutralResetBars` velas (input, 30), vuelve a NEUTRO.

2. **Stop Loss cercano y acotado.**
   V72 tomaba el nivel más lejano entre varios candidatos, incluida la liquidez
   externa (mínimo de ~1 semana). Ahora el SL usa el mínimo interno de 8 velas u
   Order Block fresco, nunca más cerca que `SL mínimo x ATR` (1.2) ni más lejos
   que `SL máximo x ATR` (2.5, nuevo input).

3. **Plan final único.**
   Líneas ENTRY/SL/TP, caja de mapa, aviso vivo, panel derecho y alertas
   Telegram leen los mismos valores (`plan*V73`). Si la capa V72 tiene una
   oportunidad activa manda ella; si no, se muestra el plan del CORE como
   contexto. Antes la pantalla podía decir "ENTRAR YA · SELL" mientras las
   líneas y la alerta seguían un plan BUY.

4. **Cambio real de tendencia consistente.**
   Se detecta con `masterDir[1]`. En V72 dependía de una variable que solo se
   actualizaba en la última vela, así que en histórico/replay nunca disparaba.

5. **FVG con mitigación real y Order Blocks con caducidad.**
   Un solo rastreador de FVG (el que antes era solo visual) alimenta ahora la
   lógica. Un hueco lleno deja de existir. Los OB caducan a `obMaxAgeBars`
   velas (input, 150). Las cajas POI del gráfico caducan a `poiMaxAgeBars`
   (input, 300).

## Correcciones técnicas

- `request.security`: de 45 llamadas a 13. Una tupla por temporalidad
  (`f_mtf`), ATR macro sin uso eliminado, rangos macro en tuplas.
- `ta.sma(volume)` y `ta.highest/lowest` del heatmap pasan al ámbito global.
- Indentación de continuación unificada a 5 espacios en el bloque ICT.
- JSON de alerta: clave `poi` duplicada corregida (`poi` + `poi_detail`),
  nuevo campo `runner` (lo lee `server.py`), `tp3`/`tp4`/`tp5`, `exec_score`,
  `context`, `plan_source`. Comillas y barras invertidas se sanean.
- Textos "NaN" evitados con `f_px` / `f_range` cuando un nivel es `na`.

## Alertas

- `BUY` / `SELL`: se disparan con "ENTRAR YA" del semáforo (`execEnter*V72`).
- `PRE_BUY` / `PRE_SELL`: con "RECHAZO · ARMADO" (`execArmed*V72`).
- En TradingView: crear la alerta con "Cualquier llamada a la función alert()".

## Código eliminado (sin efecto en pantalla)

Motores V42-V46 (sniper, memoria adaptativa, retest V45 salvo zonas, reacción
V46), bloque de avisos `notice*`/`persistent*` nunca renderizado, filtro
Nadaraya-Watson sin salida, textos sin consumidor, inputs sin efecto
(`showOnePanel`, `panelSize`, `showTfPanel`, `uiPrivacyV65`, `showDecisionUX`)
y ~70 líneas de `alertcondition` comentadas.

## Pendiente de validar en TradingView

- Compilación y advertencias.
- Que `masterDir` ahora sí cambia en un gráfico con tendencia clara.
- Que el SL dibujado queda entre 1.2 y 2.5 ATR de la zona de entrada.
