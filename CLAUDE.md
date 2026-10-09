# Instrucciones del proyecto para la IA

Toda sesión de IA que trabaje en este repositorio lee esto primero. Una orden nueva del dueño manda sobre este archivo; si la orden cambia una regla de aquí, se actualiza este archivo en el mismo cambio.

## 1. Qué es

- **Xnova para Telegram:** llevar Xnova, un juego web de estrategia espacial en el que se farmea (de la familia de OGame), a **Telegram, en formato de texto**.
- **Es un proyecto nuevo y aparte.** No se mezcla con ningún otro proyecto del dueño (ni Lost Realms / RPGDungeon ni TowerWars): no se leen sus documentos ni se toman sus reglas para este (pedido del dueño, 8-oct-2026).
- **Estado:** investigación terminada en [investigacion/](investigacion/README.md). Primera versión del bot escrita en `xnova_bot/`, lista para Railway (ver [README](README.md)). Las reglas que se apartan de Xnova son decisiones provisionales, listadas en el README: el dueño las confirma o las cambia.

## 2. Notion: todo se sube solo y como texto

Pedido del dueño (8-oct-2026):

1. **Todo se sube a Notion automáticamente**, sin esperar a que el dueño lo pida: investigación, diseño, decisiones, preguntas, código y lo que el dueño mande para el proyecto.
2. **Se sube como texto escrito directamente en una página de Notion.** Nunca como archivo adjunto ni como documento aparte (Word, PDF, Markdown, documentos de Claude). El código va en bloques de código dentro de la página.
3. **Antes de subir, verificar que va como texto en la página.** Si no es así, parar y hacerlo directamente en una página.
4. **Dónde:** en la página [Xnova para Telegram — Investigación](https://app.notion.com/p/3f3476db16ab81e4bd89dc28f9b88a51), con una subpágina por tema. Lo nuevo va como subpágina o como sección dentro de ella.
5. **Después de subir, leer la página en Notion** para confirmar que se ve bien (tablas, enlaces entre páginas, nada cortado).
6. **El repositorio y Notion dicen lo mismo.** Lo que cambia en uno se cambia en el otro en el mismo trabajo.

## 3. Cómo hablar con el dueño

- **Siempre en español.**
- **Habla por voz:** las transcripciones llegan revueltas. Se interpreta la intención sin pedirle que repita, y si la interpretación cambia algo importante, se dice cuál se tomó.
- **Respuestas en lenguaje de resultado:** qué quedó hecho, qué falta y qué necesita de él.

## 4. Código

- **Código en inglés; lo que lee el jugador, en español.** Los nombres y textos fijos van en `xnova_bot/texts.py`; los informes, en `xnova_bot/reports.py`; las pantallas, en `xnova_bot/bot/screens.py`. Los avisos y errores que arma el juego están en `xnova_bot/game.py`.
- **Los números del juego** están en `xnova_bot/data/elements.py` y `xnova_bot/config.py`. Si se mueve uno, se dice en el README y en Notion.
- **Las migraciones de la base de datos solo agregan.** Nunca se borran tablas, columnas ni partidas sin permiso del dueño.
- **Antes de subir:** `pytest` (incluye el bot completo contra un Telegram simulado) y `pyflakes xnova_bot tests`.
- **Credenciales nunca en el repositorio:** solo los nombres de las variables en `.env.example`.
- **Railway:** el dueño crea y configura el servicio. No se toca Railway sin su permiso.

## 5. Git

- Se trabaja en la rama asignada a la sesión. Nunca `push --force`.
- El repositorio todavía no tiene rama `main`: crearla necesita el sí del dueño.
