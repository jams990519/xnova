# Xnova para Telegram

Proyecto nuevo y aparte: **Xnova**, el juego web de estrategia espacial en el que se farmea (de la familia de OGame), llevado a **Telegram, en formato de texto**.

| | |
|---|---|
| **Estado** | Código completo de la primera versión, listo para ponerlo en Railway |
| **Idioma** | Español |
| **Notion** | [Xnova para Telegram — Investigación](https://app.notion.com/p/3f3476db16ab81e4bd89dc28f9b88a51). Todo lo del proyecto se sube ahí como texto (ver [CLAUDE.md](CLAUDE.md)) |

## Qué hay aquí

| Carpeta o archivo | Qué tiene |
|---|---|
| [investigacion/](investigacion/README.md) | Todo lo que se encontró sobre Xnova y los juegos parecidos: historia, reglas con sus números, cómo funciona el farmeo, qué enganchaba y qué espantaba a los jugadores, y qué existe ya en Telegram |
| `xnova_bot/` | El código del bot |
| `tests/` | Las pruebas: reglas del juego y el bot completo contra un Telegram simulado |
| `Dockerfile` | Cómo arma Railway el servidor |
| `.env.example` | Los nombres de las variables (sin valores) |

---

## Ponerlo en marcha en Railway

Son cinco pasos. No hace falta dominio ni configurar nada más.

1. **Crear el bot en Telegram.** Abre [@BotFather](https://t.me/BotFather), escribe `/newbot`, elige un nombre y un usuario (tiene que terminar en `bot`). BotFather te da un **token**, algo como `123456:ABC...`. Guárdalo: es la llave del bot.
2. **Crear el servicio en Railway.** En Railway: *New Project* → *Deploy from GitHub repo* → elige `jams990519/xnova`. Railway encuentra el `Dockerfile` y arma el servidor solo.
3. **Poner el token.** En el servicio, pestaña *Variables*, agrega `TELEGRAM_BOT_TOKEN` con el token de BotFather. Opcional: `ADMIN_IDS` con tu número de usuario de Telegram (te lo da [@userinfobot](https://t.me/userinfobot)) para usar `/admin` y `/aviso`, y `TIMEZONE` con tu zona horaria (por ejemplo `America/Bogota`).
4. **Conectar un volumen.** Clic derecho en el lienzo del proyecto (o `⌘K`) → *Volume* → conéctalo al servicio y ponle de ruta de montaje **`/data`**. Ahí se guarda la base de datos. **Sin volumen, todas las partidas se borran cada vez que el servicio se vuelve a desplegar.** El bot detecta el volumen solo.
5. **Desplegar y probar.** Railway despliega. En *Logs* debe aparecer `Xnova bot started`. Abre tu bot en Telegram y escribe `/start`.

**Para actualizarlo:** cada cambio que se sube a la rama conectada se despliega solo. Las partidas quedan guardadas en el volumen.

**Copias de seguridad:** Railway permite hacer copias del volumen, manuales o automáticas (ver su guía de *Backups*). Recomendado: una copia diaria.

### Variables

| Variable | Para qué | Por defecto |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | **Obligatoria.** El token del bot | — |
| `ADMIN_IDS` | Tu número de usuario de Telegram, para `/admin` (estado del servidor) y `/aviso texto` (mensaje a todos). Varios, separados por comas | nadie |
| `TIMEZONE` | Zona horaria de las horas en los mensajes | `UTC` |
| `GALAXIES` / `SYSTEMS` | Tamaño del universo | 3 galaxias × 100 sistemas |
| `ECONOMY_SPEED` / `FLEET_SPEED` | Velocidad de la economía y de las flotas | ×1 y ×1 |
| `MAX_PLANETS` | Planetas por jugador | 9 |
| `NOOB_RATIO` / `NOOB_POINTS_LIMIT` | Protección de novatos: proporción de puntos y hasta cuántos puntos dura | 5 y 50.000 |
| `BASH_LIMIT` | Ataques máximos al mismo planeta en 24 horas | 6 |
| `VACATION_MIN_HOURS` | Mínimo del modo vacaciones | 48 |
| `DEBRIS_SHIPS` / `DEBRIS_DEFENSE` | Parte de lo destruido que queda como escombros | 0,3 y 0 |
| `DATA_DIR` | Carpeta de la base de datos (en Railway no hace falta: usa el volumen) | volumen o `data/` |

**Importante:** solo debe haber **un** servicio corriendo con el mismo token. Si hay dos, Telegram los hace pelear por los mensajes.

---

## Qué trae esta primera versión

- **Cuenta y planeta.** `/start`, nombre de comandante, planeta inicial de 163 campos. Los jugadores nuevos nacen de a tres por sistema, para que tengan vecinos.
- **Recursos.** Metal, cristal, deuterio y energía, que se producen cada hora aunque nadie esté conectado. Porcentaje de producción por mina, almacenes y avisos de almacén lleno.
- **Edificios** (18), **investigaciones** (16), **naves** (14) y **defensas** (8), con los costos, tiempos y requisitos de Xnova.
- **Hangar con cola:** las naves y defensas salen una por una con el tiempo.
- **Flotas:** atacar, espiar, transportar, desplegar, colonizar, reciclar escombros y expediciones. Se envían paso a paso con botones: naves → destino → misión → velocidad → carga → confirmar. Se pueden hacer volver.
- **Batallas** por rondas con fuego rápido, escudos y explosiones, botín, escombros, reconstrucción de defensas y **lunas**.
- **Espionaje** con informe por niveles y, desde el informe, **⚡ Saqueo rápido**: manda justo las naves de carga necesarias.
- **Galaxia:** el sistema completo en un mensaje, con marcas de inactivos (i)/(I), vacaciones (v), novatos (n) y demasiado fuertes (f). Escribir unas coordenadas (`1:23:8`) abre esa posición.
- **Avisos automáticos:** ataque en camino, espionaje, informes de batalla, flotas que vuelven, construcciones terminadas (se pueden apagar).
- **Protección:** novatos (proporción 5 a 1), máximo 6 ataques al mismo planeta cada 24 horas, modo vacaciones de 48 horas como mínimo, inactivos atacables.
- **Oficiales de Xnova:** experiencia de minero y de saqueador, puntos de oficial y 11 oficiales.
- **Ranking** de jugadores y de alianzas.
- **Alianzas:** crear, unirse con código, mensaje a todos, expulsar, salir.
- **Mensajes privados** entre jugadores.
- **Administración:** `/admin` y `/aviso`.

## Reglas: de dónde salen los números

Los números son los de Xnova, sacados de su código (ver [Reglas y números](investigacion/02-reglas-y-numeros.md)). Donde el código de Xnova tenía un error, se usa la regla de OGame clásico. **Son decisiones provisionales: se pueden cambiar.**

| Tema | Xnova | En este bot |
|---|---|---|
| Combate | Por grupos, con fuego rápido fijo y tecnologías cruzadas | Nave por nave, como OGame: escudo, 1 % mínimo, explosión bajo 70 %, fuego rápido con probabilidad |
| Escombros | 60 % de las naves y 0 % de las defensas (por error) | 30 % de las naves, 0 % de las defensas (OGame) |
| Botín | La mitad, sin volver a llenar la bodega | La mitad, rellenando la bodega (OGame) |
| Investigación | 5 veces más rápida | Tiempo de OGame clásico |
| Almacenes | 10 millones × 1,5^nivel | 100.000 + 50.000 × (⌈1,6^nivel⌉ − 1) (OGame clásico) |
| Planetas por jugador | Sin límite (9.000) | 9 |
| Ataques al mismo planeta | Sin límite en el código | Máximo 6 en 24 horas, bloqueado automáticamente |
| Modo vacaciones | 24 horas | 48 horas (OGame) |
| Velocidad de naves | La pequeña de carga y el bombardero sumaban mal el bono | Fórmula de OGame |
| Espionaje con niveles iguales | Usaba el nivel en vez de las sondas | Usa las sondas |
| Expediciones | 1 de cada 11 pierde la flota; la carga se cuenta con una nave por tipo | Igual que Xnova (lo de la carga funciona como tope) |
| Oficiales | Se ganan con experiencia | Igual que Xnova |
| Supernova y oficiales finales | A medio terminar | No incluidos |

## Lo que falta (próximas versiones)

- Ataque en grupo (SAC) y defender el planeta de un aliado (mantener posición).
- Misiles interplanetarios y de intercepción (ocultos por ahora).
- Sensor phalanx, salto cuántico y destrucción de lunas.
- Los oficiales finales de Xnova (Búnker, Destructor, Saqueador, Emperador) y la nave Supernova.
- Bloquear a un jugador en los mensajes privados.
- Nombres propios para el juego (por ahora se usan los de la versión en español de OGame).

## Para programadores

- **Python 3.12** y [python-telegram-bot](https://python-telegram-bot.org) 21. Base de datos **SQLite**.
- El bot pregunta a Telegram por mensajes nuevos cada pocos segundos, así que no necesita dirección web.
- Un reloj interno procesa cada 3 segundos lo que vence: construcciones, investigaciones y flotas, en orden de tiempo. Si el servidor estuvo apagado, al volver procesa todo lo atrasado en orden.
- El código está en inglés y los textos para el jugador en español, en `xnova_bot/texts.py`.

| Carpeta | Qué hace |
|---|---|
| `xnova_bot/data/elements.py` | Los números de cada edificio, investigación, nave, defensa y oficial |
| `xnova_bot/engine/` | Reglas puras: fórmulas, combate, espionaje y expediciones |
| `xnova_bot/db.py` | Base de datos y migraciones (solo agregan, nunca borran) |
| `xnova_bot/game.py` | El juego: todas las acciones y los eventos con tiempo |
| `xnova_bot/reports.py` | Textos de los informes |
| `xnova_bot/bot/` | Telegram: pantallas (`screens.py`) y manejo de mensajes y botones (`handlers.py`) |
| `xnova_bot/main.py` | Arranque |

**Probar en tu computadora:**

```bash
pip install -r requirements-dev.txt
pytest                      # 23 pruebas, incluido el bot completo contra un Telegram simulado
TELEGRAM_BOT_TOKEN=... python -m xnova_bot.main
```
