# IMPULXOR V75 — POI · ESTRUCTURA · EJECUCIÓN EN VIVO

Archivos: `IMPULXOR_V75.pine` y copia `IMPULXOR_V75.txt` para pegar en TradingView.
Base: V73 (auditoría aplicada) + motor POI/estados de V74.1 corregido + capa de
estructura inspirada en los conceptos de los scripts de referencia (implementación
propia, sin copiar código de terceros).

## Una sola autoridad operativa

- La máquina de estados V75 (`stateCodeV73`) manda en el panel derecho, el panel
  izquierdo, las cards, el móvil, la caja central, las líneas ENTRY/SL/TP y las
  alertas. Ya no hay dos motores en pantalla.
- Estados: 0 evento manual · 10 lateral · 11/12 esperar · 21/22 preparar ·
  31/32 ENTRAR YA · 41/42 posición viva · 51/52 retroceso con posición ·
  61/62 proteger · 63/64 objetivo final · 65/66 stop tocado · 71/72 ya se fue.
- "YA SE FUE" (71/72) ya no es NO TRADEAR y nunca pisa una posición viva.
- "ENTRAR YA" dura `Velas que dura ENTRAR YA` (3) mientras la entrada siga válida,
  no una sola vela.

## POI institucional

- Order Block con relevancia de volumen, FVG con mitigación y caducidad,
  intersección OB+FVG, Premium/Discount del rango, EQH/EQL, barridas.
- Sin OB ni FVG, la zona diaria solo puntúa si hubo barrida o absorción real.
- Umbrales editables: calidad POI para PREPARAR (50) y ENTRAR (58), score vivo
  para ENTRAR (60). Bajarlos da más entradas; subirlos las filtra.

## Posición viva y gestión

- Entrada al cierre del estado 31/32. SL único acotado (0.8 a 2.5 ATR, inputs).
- TP1 a TP5 con marca ✓ al tocarse. SL se mueve a entrada tras TP1 y escalona
  tras TP2+ (input). Línea punteada con el SL original.
- Salida por stop, objetivo final (TP5), tiempo máximo (80 velas) o entrada
  contraria. Estadística en vivo: señales, ganadas (TP1+), perdidas, acierto.

## Capa de estructura en el gráfico

- Swing: pivotes HH/HL/LH/LL, líneas BOS/CHoCH con etiqueta.
- Interna: iBOS/iCHoCH con pivote corto.
- EQH/EQL en gráfico, SFP (fallo de swing), Premium/Equilibrium/Discount,
  PWH/PWL/PMH/PML, fondo de Killzones (Asia/London/NY), cajas riesgo/beneficio.
- Objetos históricos limitados por `Máx. objetos por capa` (8); el resto se
  repinta solo en la última vela.

## Panel nuevo ESTRUCTURA & SETUP (abajo izquierda)

Estructura swing e interna, último evento y su calidad (FUERTE/DÉBIL), grado
del setup A/B/C, zona del rango, EQH/EQL, sesión, ratio R a TP1, trade abierto,
señales y acierto en vivo.

## Alertas

- BUY/SELL al abrir posición (31/32) con entry/SL/TP del plan único y campo
  `runner`. PRE_BUY/PRE_SELL en 21/22. Alertas adicionales: TP1, stop, objetivo.
- Crear en TradingView con "Cualquier llamada a la función alert()".

## Rendimiento

- 15 llamadas `request.security` (7 MTF + H3 + D + 2 macro + W + M).
- Sin código muerto: motores V42-V46, avisos no renderizados, NW, inputs sin efecto.

## Pendiente de validar en TradingView

Compilación, que aparezcan entradas 31/32 en un gráfico M5/M15 con tendencia, y que
el SL dibujado coincida con el del panel y la alerta.

## V75.1 — aportes integrados desde la rama "LIVE POINTS + POI"

- POINTS vivos: círculo bajo/sobre la vela cuando hay reacción en POI con
  calidad ≥ 48 (color pleno si ≥ 78). Input "POINTS vivos".
- Etiqueta BUY / SELL sobre la vela exacta donde se abre la posición.
- Sesgo general MTF ponderado (`marketBias*`): alimenta MODO y SESGO del panel
  izquierdo, PULSO de las cards, LECTURA MADRE del móvil, la caja central y el
  campo `market_bias` de la alerta. No activa entradas por sí solo.
- ASERTIVIDAD y CALIDAD muestran la confianza viva del estado (score del
  motor cuando hay preparar/entrar; si no, el mayor entre sesgo MTF y calidad POI).
- Zonas SELL/BUY del panel izquierdo muestran el POI real con su tipo.
- EMAs ocultas por defecto (input), aviso vivo legacy y EXP legacy apagados.

## V75.2 — POINTS visibles y cajas BUY / SELL (solo capa visual)

- POINT BUY / POINT SELL como etiqueta pegada a la vela del toque con reacción,
  en cian y rosa como la referencia, con el % de calidad del POI. Permanecen en el
  gráfico (máx. 3 por zona, 60 en pantalla, inputs). Umbral de calidad 45 (input).
- La vela de entrada del motor lleva "ENTRAR BUY" / "ENTRAR SELL" en verde/rojo,
  distinta del POINT para no confundir reacción con orden.
- Las cajas POI ahora dicen "BUY ZONE · DEMANDA OB/FVG" y "SELL ZONE · OFERTA ...",
  con línea media punteada, fuerza y volumen relativo del OB. Colores editables.
- Motor, paneles y alertas sin cambios.
