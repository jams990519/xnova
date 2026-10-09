# Investigación: Xnova

> [Volver al inicio](../README.md)

Todo lo que se encontró sobre **Xnova**, el juego web de estrategia espacial en el que se farmea, y sobre las versiones parecidas, para llevarlo a **Telegram en formato de texto**. De aquí salen los números del bot, que está en `xnova_bot/` (cómo ponerlo en marcha: [README del proyecto](../README.md)). Las reglas del bot que se apartan de Xnova son decisiones provisionales.

## Lo más importante

1. **Xnova es una copia de código abierto de OGame** (el juego de Gameforge de 2002). Viene de UGamela (2004), nació en 2007 y su versión clave, la 0.9a, es francesa (2008). Es el OGame clásico, sin las novedades de los últimos años.
2. **Es una familia entera:** UGamela → Xnova → XG Proyect (Argentina) y 2Moons → SteemNova, y ahora OGameX. Todas comparten las reglas; cambian los extras. La que sigue viva es **XG Proyect 4**.
3. **OGame sigue abierto** y creció: clases, formas de vida, logros y app móvil.
4. **El corazón es el farmeo:** subir minas, espiar, atacar planetas (sobre todo de jugadores inactivos), llevarse la mitad de sus recursos y reciclar los escombros.
5. **Las reglas son números claros:** costos que crecen de forma exponencial, producción por hora, combate por rondas, botín del 50 %, escombros, lunas. Están todas, con sus tablas, en [Reglas y números](02-reglas-y-numeros.md), sacadas del propio código de Xnova.
6. **Xnova tiene algo propio:** oficiales que **se ganan jugando**, con experiencia de minero y de saqueador. En OGame se pagan con dinero real.
7. **El código de Xnova tiene errores** que los jugadores asumieron como reglas: escombros del 60 % de las naves y 0 % de las defensas, tecnologías de escudo y casco cruzadas, expediciones que pierden toda la flota 1 de cada 11 veces, entre otros.
8. **Lo que espantaba a los jugadores:** tener que conectarse a horas fijas para no perder la flota, ser la granja de los más fuertes, pagar para ganar, multicuentas y programas que juegan solos.
9. **En Telegram casi no hay nada parecido.** El único juego de este tipo que se encontró es SpaceHunt (@SpaceHuntBot), en inglés y ruso, con poca difusión.
10. **Xnova ya es casi todo texto y números,** así que cabe bien en Telegram. Lo difícil será mandar flotas (en la web son tres pantallas). La gran ventaja es que el bot puede **avisar solo** cuando viene un ataque.

## Páginas de la investigación

| # | Página | Qué tiene |
|---|---|---|
| 1 | [Historia y familia](01-historia-y-familia.md) | De dónde sale Xnova, todas las versiones parecidas, cómo está OGame hoy y qué dicen las licencias |
| 2 | [Reglas y números](02-reglas-y-numeros.md) | El universo, los recursos y su producción, edificios, investigaciones, naves, defensas, tiempos, viajes, combate, botín, escombros, lunas, espionaje, misiones, expediciones, protección, oficiales, los errores del código y lo que agregó 2Moons |
| 3 | [El farmeo](03-el-farmeo.md) | El saqueo paso a paso con un ejemplo con números, los estilos de jugador, cómo se defiende el farmeado y las reglas que lo frenan |
| 4 | [Lo que enganchaba y lo que espantaba](04-lo-que-enganchaba-y-lo-que-espantaba.md) | Los ganchos, las quejas de los jugadores, cómo se cobraba y 11 lecciones |
| 5 | [Juegos parecidos y Telegram](05-juegos-parecidos-y-telegram.md) | Comparación de versiones, lo que ya existe en Telegram, qué cambia al pasar al texto y lo que habrá que decidir |
| 7 | [Capturas que mandó el dueño (9-oct)](07-capturas-del-dueno.md) | Lo que muestran dos capturas de un bot de XNova en Telegram y en qué se diferencia del nuestro |

## Cómo se hizo

- **El código de Xnova** ([xmke/xnova](https://www.github.com/xmke/xnova), una copia de XNova:Legacies) se leyó directamente: de ahí salen todos los números. También se leyó el de [2Moons](https://github.com/jkroepke/2Moons) y el de [XG Proyect](https://github.com/XGProyect/XG-Proyect-v3.x.x).
- **La historia, las reglas de OGame y las opiniones de los jugadores** salen de búsquedas en internet: cada documento tiene sus fuentes al final.
- **Lo que no se pudo comprobar** se dice en el texto. Varias páginas (Wikipedia, la wiki de OGame) no se pudieron abrir directamente; sus datos vienen de los resúmenes de búsqueda.
