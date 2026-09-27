# Auditoría IMPULXOR V77.5 (Pine Script v6)

Alcance: revisión estática del script `IMPULXOR_V77.5.pine` (3.369 líneas). No se pudo compilar fuera de TradingView, así que los hallazgos de compilación son por lectura. Se revisó lógica del motor, repintado, gestión de posición viva, estadística, alertas/webhook y capa visual.

## Resumen

- Sin errores de sintaxis v6 evidentes. 15 llamadas a `request.security` (límite 40), 8 tablas, ~260 ámbitos locales. El riesgo real de compilación es el tamaño compilado por el volumen de código muerto y ternarios de texto.
- El motor de entradas es consistente entre histórico y tiempo real (estado `var` se confirma al cierre de vela y las alertas usan `once_per_bar_close`), **salvo por el marco H3**, que sí repinta (hallazgo 1).
- La estadística "ACIERTO TP1+" es optimista por construcción (hallazgo 2). No debe leerse como probabilidad de ganar.
- El webhook actual (`server.py`) es compatible: usa `signal`, `price`, `entry_zone`, `runner`, `risk`, y ambos mensajes (entrada y PRE) los incluyen.

## Hallazgos por prioridad

### ALTA

1. **H3 (d180) repinta y es inconsistente con el resto de marcos.** Línea 189: `request.security(..., "180", [close, ema, ema, rsi, ...], lookahead_off)` sin desplazamiento `[1]`. Todos los demás marcos usan `f_mtf` con `[1]` + `lookahead_on` (vela confirmada). En histórico, `h3Close`, `h3E9`, `h3E21` y `r180` toman el valor final de la vela de 3h, que en vivo no se conoce hasta que cierra. Afecta a `d180`, `motherBias`, `institutionalBias*`, `macroContextDirV73`, `strongLow/HighV74`, `ictBullChoch/BearChoch`, `ictBias*`, `fractal*`. Resultado: el histórico se ve mejor que el comportamiento real.
   Corrección: pedir `[close[1], ema[1], ema[1], rsi[1]]` con `lookahead_on` (como `f_mtf`), dejando `ta.highest(high[1],36)`/`ta.lowest` como están.

2. **"ACIERTO (TP1+)" infla el rendimiento.** `f_tpBuy` fija TP1 en `max(entrada + 0.60·ATR, máximo interno de 8 velas)`; el SL sale de `f_slBuy(poiBuyLoV74)` (mínimo 0.80·ATR bajo el **borde inferior del POI**, no bajo la entrada, y la entrada puede estar hasta ~0.55·ATR por encima del POI). En muchos casos el R:R en TP1 es < 1. Además: un toque de mecha cuenta como TP; no hay spread ni slippage; tras TP1 el SL pasa a entrada y un cierre en BE sigue contando como "✓". El panel lo etiqueta como "acierto", lo que invita a leerlo como win-rate. Recomendación: mostrar también R medio o exigir TP1 ≥ 1R, y etiquetar como "% que tocó TP1".

3. **Eventos TP1 / STOP / OBJETIVO no llegan al webhook.** Solo existen como `alertcondition` (líneas ~2475-2477); no hay `alert()` para ellos. Con una alerta "Cualquier llamada a alert()" Telegram solo recibe BUY/SELL/PRE. Si se quieren en Telegram hay que añadir `alert(...)` para `alertTp1V75`, `alertStopV75`, `alertTargetV75`.

### MEDIA

4. **La ventana "ENTRAR YA" llega tarde.** El motor abre la posición al cierre de la vela de señal (precio = `close`). El estado 31/32 se muestra durante `entryWindowBarsV75` (3) velas **después** de esa apertura y el plan dibuja la entrada en ese cierre pasado. Un usuario que entre al ver el panel lo hace 1–3 velas más tarde que la estadística registrada. La alerta sí sale en la vela correcta.

5. **La volatilidad extrema no bloquea entradas.** `eventBlockV61`/`volExtremeV61` solo alimentan texto (`manageTxtV61`, que además no se usa; `spikeRiskV73` solo cambia `executionRisk`/`eventTxtV73`). El único bloqueo real es el manual (`manualNewsRisk`). Si la intención del input "Umbral evento/volatilidad" era bloquear, falta añadir `not spikeRiskV73` a `enterBuyRawV73`/`enterSellRawV73`.

6. **Payload de alerta muy grande.** `f_msgV73` genera ~3.000 caracteres y ~75 claves; el servidor usa 5. Está cerca de límites prácticos de mensaje de alerta y encarece cada envío. Recomendación: reducir a las claves que consume el backend (entrada, SL, TP1–TP5, estado, acción, contexto, sesión, riesgo).

7. **Dos rastreadores de Order Block con vidas distintas.** `bullObFresh` (via `ta.valuewhen`, caduca a `obMaxAgeBars`=150, nunca se invalida por precio) alimenta SL, breaker y PD-array ICT; `bullObValidV74` (caduca a `poiMaxAgeBars`=300 y se invalida si el cierre lo perfora) alimenta el POI. El SL puede anclarse a un OB que el POI ya descartó, o el POI usar un OB que ICT ya considera viejo. Unificar en uno.

8. **El rastreador FVG guarda solo el último gap por lado.** Un FVG nuevo sustituye a uno anterior no mitigado. Es aceptable como diseño, pero hace que "FVG vivo" en el panel no sea el más cercano al precio.

9. **BUY bloqueado en rupturas.** `buyChaseBlockV74` exige `buyRoomAtrV74 ≥ 0.65` hacia `ictBSL` (máximo externo H3/H4). Cuando el precio hace máximos nuevos, el espacio es ≤0 y BUY queda bloqueado (simétrico en SELL). El motor solo opera dentro del rango externo; conviene saberlo antes de usarlo en tendencia fuerte.

### BAJA

10. `mtfTotalWeightV75 = 110.0` pero los pesos suman 100: "MODO DEL MERCADO" nunca pasa de 91 %. Cambiar a 100.

11. Símbolos sin volumen (índices/CFD de algunos brokers): `volBase20` es `na`, así que `volRelV73` es `na` y el POI pierde el bono de volumen (hasta 8 puntos). No rompe nada, pero la calidad POI queda sistemáticamente más baja.

12. Marco "M1" desde gráficos superiores: los datos intrabar de 1 min son limitados, `d1` será `na` en casi todo el histórico y el reparto de pesos MTF cambia entre histórico y vivo. En marcos inferiores al del gráfico, el `[1]` hace que se lea la penúltima vela intrabar.

13. Versionado incoherente: título "V77.5", pero `source` de la alerta es `IMPULXOR_V75_POI_STRUCTURE_LIVE` y los `alertcondition` dicen "V75". Si el backend filtra por `source`, mantenerlo consistente a propósito.

14. Etiquetas que sugieren precisión que no existe: "ASERTIVIDAD %" es el score vivo, no una tasa de acierto; "x/7 LISTOS" es `round(score/100·7)`, no un checklist real. Aclarar el rótulo o quitar el "/7".

15. El reloj "VELA mm:ss" solo se actualiza cuando llega un tick, no cada segundo.

## Código muerto (impacta tamaño compilado)

- Inputs sin uso: `manualNewsTitleV63`, `manualNewsLevelV63`, `imgZoneHistoryV76`.
- Funciones sin uso: `f_clean`, `f_barV63`, `f_tfBgV63`, `stars`, `starsNum`, `tfDirTxt`; `f_imgZonesUpdateV76` solo se llama bajo `if false and ...`.
- Dos `plotshape(false and ...)` al final del archivo nunca dibujan.
- El bloque de `while` que borra etiquetas "legacy" con el dashboard activo borra objetos que en ese modo nunca se crean.
- ~40 variables calculadas y nunca leídas, entre ellas: `deltaSynthetic`, `continuationReal`, `entryBuyFrom/To`, `entrySellFrom/To`, `manageTxtV61`, `volTxtV61`, `eventTxtV73`, `stateSlTxtV73`, `stateTargetTxtV73`, `uxEstado`, `uxFase`, `uxSpaceTxt`, `uxColorV75`, alias `exec*V72`, `macroContextDirV72`, `buy/sellLocationV72`, `reactionTxtV65`, `reactionColorV65`, `zoneProxPctV65`, `marketBiasSideV75`, `imgZoneWordV76`, `imgPullbackTxtV767`, `imgBuy/SellKindV768`, `imgBuy/SellInsideV771`, `imgBuy/SellFvgPctV771`, `imgExhaustDirV77`, `imgSeqDirV771`, `imgOperationEnabledV766`, `imgPhaseColV77`, `uiDesktopV65`, `v65Purple`, `dayHigh`.

Limpiar esto reduce el riesgo de "script too large" y el tiempo de cálculo en M1.

## Lo que está bien

- Marcos MTF con `[1]` + `lookahead_on` y PDH/PDL con el mismo patrón: no repintan.
- Estado de posición y estadística en `var`: en tiempo real se confirma al cierre, coherente con `alert.freq_once_per_bar_close`.
- Si TP y SL caben en la misma vela prevalece el SL.
- Divisiones protegidas (`rng`, `bodySafe`, `planRiskV75`, `heatStep`, `imgPressDenV76`).
- Objetos de la última vela se borran y redibujan en cada actualización; límites declarados (500/500/250) holgados.
- JSON de alerta válido: `f_jsonSafe` escapa comillas y barras; no hay saltos de línea en los campos enviados.

## Cambios sugeridos en orden

1. Arreglar la request H3 (hallazgo 1).
2. Añadir `alert()` para TP1/STOP/OBJETIVO si se quieren en Telegram (3).
3. Decidir si la volatilidad extrema bloquea entradas (5).
4. Re-etiquetar o endurecer la métrica TP1+ (2) y `mtfTotalWeightV75 = 100` (10).
5. Unificar rastreador de OB (7) y recortar el payload (6).
6. Limpieza de código muerto.
