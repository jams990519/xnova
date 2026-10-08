# 5 · Los juegos parecidos y lo que ya existe en Telegram

> **Investigación** · [Volver al índice](README.md)

## 1. Las versiones parecidas, lado a lado

Todas comparten el mismo esqueleto: minas, investigaciones, flotas, espionaje, saqueo, escombros, lunas y alianzas. Cambian los extras y la forma de cobrar.

| | OGame (hoy) | Xnova | XG Proyect | 2Moons | SteemNova | OGameX |
|---|---|---|---|---|---|---|
| **Qué es** | El original, de Gameforge | Copia libre del OGame de 2008 | Copia libre argentina | Xnova muy ampliado | 2Moons con criptomoneda | Copia nueva del OGame de antes de 2022 |
| **Sigue vivo** | Sí | No (archivado en 2023) | Sí (versión 4, 2026) | No (desde 2019) | No se sabe | Es reciente (usa Laravel 12) |
| **Licencia** | Cerrado | GPL 3 | GPL 3 | MIT | MIT | Código abierto; dice que el arte es de Gameforge |
| **Clases de jugador** | 3 | No | No | No | No | No |
| **Formas de vida** | Sí (2022) | No | No | No | No | No |
| **Oficiales** | Con materia oscura (pagando) | **Ganados con experiencia** | Con materia oscura | Con materia oscura | Con materia oscura | Con materia oscura |
| **Naves propias** | Las de clase | Supernova | — | Luna Negra, Gigarreciclador, Nave de materia oscura y otras | Las de 2Moons | — |
| **Cobra con** | Materia oscura | Nada | Materia oscura | Materia oscura | Paga criptomoneda al jugador | — |

**Otros juegos del mismo tipo** (de navegador, no copias directas): Astro Empires, Starfleet Commander y HexaGalaxy. Gameforge, que tiene interés en el tema, nombra a Astro Empires como el competidor más cercano de OGame.

## 2. Lo que ya existe en Telegram

No se encontró ninguna copia de Xnova u OGame hecha para Telegram, ni de código abierto ni cerrada. Lo más parecido:

### SpaceHunt (@SpaceHuntBot)

Es **el único juego de Telegram de este tipo que se encontró**: estrategia espacial en texto, "parecido a OGame y StarCraft".

| Qué | Cómo lo hace |
|---|---|
| **Cómo se juega** | Todo en el chat. Los botones cambian según la pantalla. Escribiendo `/` aparecen los 100 comandos más usados |
| **Comandos** | Largos y sin espacios: `newjobbuildmetalmine` para construir una mina, `canceljob...` para cancelar. Pantallas: `dashboard` (resumen del planeta), `buildings`, `missions`, `destinations` (mapa de planetas descubiertos), `units`, `log` |
| **Economía** | Minas de metal y de cristal, paneles solares. Un "Centro de tecnología" único sube de nivel y abre todo lo demás. La mina de metal tarda unos 5 minutos y la de cristal unos 7 |
| **Mapa** | No se ve el universo entero: se **descubren** planetas explorando. Explorar tiene riesgo: si te detectan, te pueden atacar |
| **Espionaje y alertas** | Un radar con **escaneo automático cada 10 minutos** avisa de ataques que vienen. El escaneo manual tarda la mitad |
| **Defensas** | Torretas que se activan o desactivan (para que no peleen y no se dañen); escudos planetarios pequeños y grandes a niveles altos de tecnología |
| **Naves** | Exploradores, cazadores, bombarderos, destructores, estrellas de la muerte y naves de carga de varios tamaños. Los viajes duran, por ejemplo, una hora |
| **Social** | Gremios con mensajes de gremio (`guildmsg`) y canales de Telegram propios; jefes que se derrotan en gremio; comercio de recursos y unidades |
| **Idiomas** | Inglés y ruso |
| **Estado** | La guía principal tiene unos 7 años. En Product Hunt tuvo 3 votos. No se pudo comprobar si sigue activo |

**Lo que enseña:** el género cabe en Telegram. Pero los comandos escritos tipo `newjobbuildmetalmine` son difíciles de recordar; los botones que cambian por pantalla son la parte que funciona.

### Otros

| Qué | Por qué importa |
|---|---|
| **Space Explorer** (@SpaceExplorerBot) | Juego espacial de Telegram, pero de otro tipo: buscar artefactos, pelear contra piratas y arena. No tiene planetas ni flotas como Xnova |
| **TBot** (programa para OGame) | No es un juego: automatiza OGame y **avisa por Telegram cuando te atacan**. Muestra que los jugadores de OGame ya querían Telegram para enterarse de los ataques a tiempo |

## 3. Qué cambia al pasar de la web al texto

Son observaciones de la investigación, no decisiones.

| De Xnova en la web | Qué implica en Telegram |
|---|---|
| **Casi todo ya es texto y números:** tablas de recursos, listas de edificios con su costo, informes | Se traduce bien a mensajes. Xnova casi no usa dibujos para jugar |
| **La vista de galaxia:** una tabla de 15 filas por sistema, con planeta, luna, escombros, jugador, alianza y acciones | Una lista por sistema cabe en un mensaje, con botones para moverse. Telegram corta los mensajes en 4.096 caracteres |
| **Mandar una flota pide tres pantallas:** elegir naves y cantidades, después destino y velocidad, después misión y recursos | Es la acción más complicada de pasar a texto. Hay que pensarla paso a paso o con atajos (por ejemplo, "repetir el último ataque") |
| **Los avisos:** en la web hay que entrar para ver si viene un ataque | En Telegram el juego puede **avisar solo**: ataque en camino, construcción terminada, flota de vuelta. Es la mayor ventaja del cambio |
| **Los informes de batalla:** tablas largas, ronda por ronda | Hace falta un resumen corto (quién ganó, qué se perdió, botín, escombros) y el detalle aparte |
| **El tiempo real:** todo corre con temporizadores de minutos a semanas | Funciona igual en Telegram. SpaceHunt ya lo hace así |
| **Atacar mientras el otro duerme** | Con avisos de ataque en el chat, el atacado se entera; pero también puede despertarlo de madrugada. Es la queja principal del género (ver [4](04-lo-que-enganchaba-y-lo-que-espantaba.md)) |
| **Programas que juegan solos** | Un bot de Telegram es fácil de automatizar desde afuera. Es un riesgo a tener en cuenta desde el principio |
| **Multicuentas** | En Telegram cada cuenta es un número de teléfono, lo que hace más difícil (aunque no imposible) tener muchas |

## 4. Lo que habrá que decidir después

La investigación deja estas preguntas abiertas para cuando se haga el diseño:

1. **¿Una copia fiel de Xnova o una versión propia?** Con los números de Xnova (y sus errores), con los de OGame clásico, o con números nuevos pensados para Telegram.
2. **¿Universo permanente o por temporadas?** OGame abre universos nuevos para que el que llega tarde pueda competir.
3. **¿Cómo se protege al que no puede estar conectado?** Protección de novatos, límite de ataques por día, modo vacaciones, avisos.
4. **¿De dónde salen las granjas?** Solo de jugadores inactivos, como en Xnova, o también de planetas del propio juego (piratas, colonias abandonadas).
5. **¿Oficiales ganados jugando (Xnova) o comprados (OGame)?** Y en general, si el juego se cobra y cómo.
6. **¿Qué tan rápido va el universo?** Xnova a velocidad ×1 dura meses; una velocidad mayor da partidas más cortas.
7. **¿Nombres propios?** Las reglas se repiten en toda la familia, pero los nombres y textos de OGame son de Gameforge.

## Fuentes

- SpaceHunt: [sitio oficial](https://spacehuntgame.com/), [comandos](https://spacehuntgame.com/commands), [guía intermedia](https://spacehuntgame.com/intermediate-guide), [guía de instalación](https://spacehuntgame.com/installation-guide), [Centro de tecnología](https://spacehuntgame.com/technology-center), [guía de Xavi Esteve](https://xaviesteve.com/6512/spacehunt-telegram-multiplayer-game/), [ficha en Telegramic](https://telegramic.org/bot/spacehuntbot/), [ficha en Botostore](https://botostore.com/c/spacehuntbot), [AlternativeTo](https://alternativeto.net/software/spacehunt/about/), [Product Hunt](https://www.hunted.space/dashboard/inspirobot/launches/spacehunt-multiplayer-game)
- Space Explorer: [sitio](https://spacebot.top/)
- TBot: [repositorio](https://github.com/ogame-tbot/TBot)
- Juegos parecidos: [lista de Gameforge](https://gameforge.com/en-GB/games/games-like-ogame-2026.html), [Starfleet Commander](https://playsfc2.com/wiki/nova)
- Versiones de la familia: ver [Historia y familia](01-historia-y-familia.md)
- Vista de galaxia y envío de flotas en Xnova: código de [xmke/xnova](https://www.github.com/xmke/xnova) (`galaxy.php`, `floten1.php`, `floten2.php`, `floten3.php`)
