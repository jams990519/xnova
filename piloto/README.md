# Piloto para @Xnova_Elite_bot

Un programa que corre **en tu computadora** y juega **@Xnova_Elite_bot** desde **tu propia cuenta de Telegram**, como si tocaras tú los botones:

- 🏗️ **Construye lo que ya alcanza**: en cada vuelta lee tus recursos, mira qué falta de tu plan y cuánto cuesta, y pone a construir lo primero de la lista que ya se puede pagar. Si lo más importante todavía no alcanza, construye lo siguiente en vez de quedarse esperando. Si la energía queda en negativo, primero la Planta solar. Si ya hay algo construyéndose, espera.
- 🔬 **Investiga** igual, con tu plan de investigación.
- 🚀 **Farmea**: vuelve a mandar las flotas que guardaste en el juego (Flotas → Mis flotas), cuando hay ranuras libres, **sin pasar de 6 ataques al mismo planeta en 24 h** (la regla del juego; por defecto se queda en 5). Si el juego no deja atacar un planeta (escudo por inactividad, protección, vacaciones…), lo salta 24 horas.
- 🛰️ Te manda a tus **Mensajes guardados** lo que hizo en cada vuelta.

Está en una carpeta aparte: no cambia en nada el bot de Xnova que corre en Railway.

> ⚠️ **Antes de usarlo:**
> - Es un programa que juega por ti. Revisa en `/guias` las reglas de @Xnova_Elite_bot: si prohíben los programas automáticos, te pueden suspender la cuenta del juego.
> - Usa tu cuenta de Telegram. El piloto va despacio a propósito (2,5 s mínimo entre toques) para no saturar al bot ni a Telegram.
> - **Nunca toca** botones de derribar, cancelar, vacaciones, reubicar, vender, comprar, retirar flotas ni nada parecido, aunque se lo pongas en la configuración.

## Cómo ponerlo en marcha (Windows)

1. **Instala Python 3.12** desde [python.org](https://www.python.org/downloads/). En el instalador marca **«Add python.exe to PATH»**.
2. **Baja el proyecto**: en GitHub, en la rama que tiene la carpeta `piloto`, botón verde **Code → Download ZIP**. Descomprímelo, por ejemplo en `Documentos\xnova`.
3. **Abre una terminal en esa carpeta** (la que tiene dentro `piloto`): en el Explorador entra a ella, escribe `cmd` en la barra de direcciones y pulsa Enter. Ahí escribe, una línea a la vez:
   ```
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r piloto\requirements.txt
   ```
4. **Saca tu api_id y api_hash** (los pide Telegram para que un programa use tu cuenta):
   entra a [my.telegram.org](https://my.telegram.org) con tu número → **API development tools** → crea una app (nombre y descripción cualquiera) → copia **App api_id** y **App api_hash**.
   **No se los pases a nadie ni los pegues en un chat.**
5. **Configura**: copia `piloto\piloto.example.toml` como `piloto\piloto.toml`, ábrelo con el Bloc de notas y pon tu `api_id` y tu `api_hash` en la sección `[telegram]`. Ahí mismo están el plan de construcción, el de investigación y el farmeo.
6. **Entra con tu cuenta** (solo la primera vez):
   ```
   python -m piloto entrar
   ```
   Te pide tu número (con +53 o +1…), el código que te llega a Telegram y, si tienes, tu contraseña de dos pasos. Queda guardado en `piloto\datos\cuenta.session`. **Ese archivo da acceso a tu Telegram: no lo compartas nunca.**
7. **Explora** (solo mira, no toca nada que gaste o ataque):
   ```
   python -m piloto explorar
   ```
   Recorre los menús del juego y guarda cómo se ven en `piloto\datos\pantallas.txt`. **Mándale ese archivo a Claude**: con él se ajusta cómo el piloto lee los recursos, los niveles y las respuestas del juego (no tiene nada secreto, solo pantallas del juego).
8. **Ensayo** (decide, pero no construye ni envía nada):
   ```
   python -m piloto jugar --ensayo --una-vez
   ```
9. **A jugar**:
   ```
   python -m piloto jugar
   ```
   Da una vuelta cada 10 minutos (se cambia en `[ritmo]`). La computadora tiene que quedar encendida y con internet. Para pararlo: **Ctrl + C**. Lo que va haciendo queda también en `piloto\datos\registro.txt`.

La próxima vez solo hace falta abrir la terminal en la carpeta y escribir `.venv\Scripts\activate` y `python -m piloto jugar`.

En Mac o Linux es igual, cambiando `py` por `python3`, `.venv\Scripts\activate` por `source .venv/bin/activate` y las `\` por `/`.

## Farmear

1. En el juego, manda una vez a mano la flota a un planeta que quieras saquear y toca **Flotas → Guardar el último envío** con un nombre, por ejemplo «Granja 1».
2. En `piloto.toml`, pon `activo = true` en `[farmear]` y un bloque por planeta:
   ```toml
   [[farmear.objetivo]]
   flota = "Granja 1"
   coordenadas = "1:45:8"
   ```
3. El piloto manda primero el que lleva más tiempo sin atacarse y deja libres las ranuras que digas en `dejar_libres`.

Recuerda las reglas del juego: no se puede atacar a quien tiene menos de 1/5 de tus puntos, y quien lleva 7 días sin entrar tiene escudo.

## Si algo no le sale

- **«No encontré el botón de …»**: el juego llama distinto a ese edificio. Pon el nombre como sale en el juego en el plan (sin emoji).
- **«No encontré "Edificios" …»**: cambia el nombre en `[etiquetas]`, o pon esa tecla entre tus seis de abajo (Mi cuenta → Teclas de abajo).
- **No construye nada aunque alcance**: el piloto no pudo leer el costo o tus recursos. Mira en `pantallas.txt` cómo escribe el juego el costo (por ejemplo «Precio:») y agrégalo en `[lectura] coste`.
- **Lee mal los recursos o la energía**: agrega en `[lectura.recursos]` la palabra o el emoji con que el juego los escribe (por ejemplo `metal = ["metal", "🔩"]`).
- Para todo lo demás: corre `python -m piloto explorar` y pásale `piloto\datos\pantallas.txt` a Claude.

## Cómo está hecho

| Archivo | Qué hace |
|---|---|
| `__main__.py` | Los comandos `entrar`, `explorar` y `jugar` |
| `client.py` | Habla con el bot desde tu cuenta (Telethon): escribe una tecla, toca un botón y espera la respuesta. Aquí está el candado de lo que nunca se toca |
| `pilot.py` | Una vuelta: construir, investigar y farmear |
| `plan.py` | Las decisiones, sin Telegram: qué toca construir y qué planeta saquear |
| `parse.py` | Lee las pantallas: recursos, niveles, cola ocupada, ranuras de flota y qué contestó el juego |
| `explore.py` | Recorre los menús sin tocar nada que haga cosas, y guarda las pantallas |
| `screen.py`, `text.py` | Busca botones sin emoji ni acentos y lee los números como los escribe el juego (1.234, 12,5k) |
| `config.py` | Lee `piloto.toml` |

Las pruebas están en `tests/test_piloto.py`: un @Xnova_Elite_bot de mentira para probar todo sin Telegram (`pytest`).
