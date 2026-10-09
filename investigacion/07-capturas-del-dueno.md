# 7 · Capturas que mandó el dueño (9-oct)

> **Investigación** · [Volver al índice](README.md)

Dos capturas de un bot de **XNova en Telegram** que mandó el dueño el 9-oct-2026, sin comentario. Aquí está lo que muestran, en texto, y en qué se diferencia del bot que ya escribimos (ver el [README del proyecto](../README.md)). **Falta que el dueño diga para qué son:** si es el modelo a copiar, otro bot suyo o solo ideas.

## Captura 1: el menú principal

**Resumen del planeta**, arriba de todo:

- 🌍 **Planeta principal** 1:98:11 · 0/202 campos · 🌡 de −35 a 5 °C
- Metal 5k · 📦 50 % · +300/h
- Cristal 3k · 📦 30 % · +150/h
- Deuterio 1k · 📦 10 % · +0/h
- ⚡ Energía 0 · 🔋 0 % en uso
- 🏆 0 (puntos)

El 📦 con porcentaje es **cuánto del almacén está lleno**.

**Menú de botones debajo del resumen** (16 botones):

| | | |
|---|---|---|
| 🏆 Ranking | | |
| Universo | Simulador | Mi cuenta |
| Alianza | Mercado | Oficiales |
| Defensa | Galaxia | Producción |
| Edificios | Investigación | Hangar |
| 🔄 Actualizar | Imperio | 🚀 Flotas |

**Mensaje de bienvenida:** «Acabas de recibir tu planeta principal. Construye minas, investiga tecnologías, arma una flota y conquista la galaxia. Todo se juega con los botones del menú. Si te pierdes, /menu te trae de vuelta aquí.»

**Elige tu clase** (con un botón «Elegir clase»): Colector (vive de las minas), Guerrero (vive de la flota) y Descubridor (vive de explorar). Es gratis; sin clase no hay bonos. Ninguna toca el combate.

**Teclado fijo de abajo:** 🏠 Menú · Edificios · 🚀 Flotas · Galaxia · Producción · Mensajes. A la izquierda del campo de texto hay un botón **📖 Guías**, y el campo dice «Usa los botones de abajo».

## Captura 2: las clases

Arriba se ven los botones **Derribar un nivel**, **Actualizar** y **Volver** (de la pantalla de un edificio).

| Clase | Bonos |
|---|---|
| ⛏ Colector: vive de las minas | Producción de minas +20 % · Energía +10 % · Bodega +25 % · Velocidad de cargueros +50 % · Cola de obras +1 |
| ⚔ Guerrero: vive de la flota | Flotas en vuelo +2 · Deuterio por viaje −25 % · Velocidad de naves de guerra +50 % · Ataques coordinados: +1 participante |
| 🔭 Descubridor: vive de explorar | Expediciones a la vez +2 · Hallazgos de expediciones +25 % · Tiempo de investigación −25 % · Alcance del sensor phalanx +2 · Nivel de espionaje +2 |

Nota del bot: «Los bonos de la clase se suman a los de los oficiales. Ninguna clase toca el combate: cambian cómo juegas, no quién gana el choque.»

## Qué tiene ese bot que el nuestro todavía no tiene

| Cosa | En las capturas | En nuestro bot |
|---|---|---|
| Menú principal | Resumen del planeta + 16 botones debajo | Teclado fijo de 12 botones y botones en cada pantalla |
| Almacén lleno | Porcentaje por recurso | Solo avisa «lleno» |
| Clases (Colector, Guerrero, Descubridor) | Sí | No. Son de OGame moderno, no de Xnova |
| Simulador de batalla | Sí | No |
| Mercado | Sí | No |
| Imperio (todos los planetas juntos) | Sí | No |
| Derribar un nivel de edificio | Sí | No |
| Cola de obras (más de un edificio en espera) | Sí (el Colector suma +1) | No: un edificio a la vez |
| Ataques coordinados | Sí (lo nombra el Guerrero) | No, queda para una próxima versión |
| Bandeja de mensajes | Botón «Mensajes» | Los mensajes llegan directo al chat |
| Guías | Botón 📖 Guías | Una sola pantalla de ayuda |
| Mi cuenta / Universo | Sí | En parte, dentro de ⚙️ Ajustes |
| Planeta inicial | 202 campos, en el sistema 98 | 163 campos; los nuevos nacen de a tres por sistema, empezando por el 1 |
