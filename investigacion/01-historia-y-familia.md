# 1 · Qué es Xnova y de dónde sale

> **Investigación** · [Volver al índice](README.md)

## En una frase

**Xnova es una copia de código abierto de OGame**, el juego de estrategia espacial de navegador que salió en 2002. Empiezas con un planeta casi vacío, construyes minas, investigas tecnologías, armas flotas, colonizas otros planetas, espías y atacas a otros jugadores para robarles recursos. Casi todo el juego gira alrededor de **farmear**: sacar recursos de tus minas y de los planetas de otros (ver [El farmeo](03-el-farmeo.md)).

## El árbol de familia

Xnova no es un juego aislado: es una rama de un árbol de copias de OGame que se pasaron el código unas a otras. Por eso hay "muchos parecidos con versiones bastante similares": comparten las mismas reglas y casi los mismos números.

| Años | Juego | Quién lo hizo | Qué aportó |
|---|---|---|---|
| 2002 | **OGame** | Alexander Rösner ("Legor"). En 2003 se unió a Klaas Kersting y de ahí salió **Gameforge** (Alemania) | El original. Lo escribió en unos dos meses como proyecto propio |
| 2004–2006 | **UGamela 0.2h** | Perberos | La primera copia de código abierto. Fue libre hasta la versión 0.2-r13; después se cerró |
| 2006–2007 | **UGamela 0.4** | Phoscur | La continuación de UGamela |
| 2007 (desde el 18 de marzo) | **XNova** (Alpha → 0.7c → 0.8a → 0.8 SP1) | Equipo XNova | Nace sobre UGamela 0.2r13, 0.3, 0.4 y 0.4++ |
| 2008–2009 | **XNova 0.9a** | XNova Group / xnova.fr (Francia) | La versión de la que salieron casi todas las demás. Sus autores principales la abandonaron en 2008 |
| 2009–2010 | **XNova:Legacies** | XNova Support Team (xnova-ng.org) | Arreglos de seguridad y parches, con licencia GPL 3. Iba a ser la antesala de *XNova:Next-Gen* (sobre Zend Framework, con licencia AGPL), que no se sabe si se terminó |
| 2008 a hoy | **XG Proyecto (XGP)** | "lucky"; después Lucas Kovacs, de Campana, **Argentina** | La rama de habla hispana. Busca parecerse lo más posible a OGame (GPL 3). En mayo de 2026 dejó la versión 3 y sigue con la **versión 4, sobre Laravel**: es la copia de la familia que sigue viva |
| 2009–2019 | **2Moons** | jkroepke | Motor muy modificado sobre XNova y XGP, con licencia MIT. El más usado por los servidores privados. Ya no se desarrolla |
| 2018–2020 | **SteemNova** | Comunidad | Sigue a 2Moons, sobre la cadena de bloques Steem. Pagaba a cada jugador en criptomoneda según sus puntos dentro de su alianza. Llegó a unos 350 jugadores activos; no se sabe si sigue abierto |
| — | **SuperNova.WS** | — | Sobre "xNova 0.8 RageRepack v226", con cambios de reglas y optimizaciones |
| hasta 2023 | **xmke/xnova** | xmke (Francia) | Copia francesa de XNova:Legacies que se estaba reescribiendo. Se archivó el 29 de enero de 2023. **Es el código que se leyó para sacar los números de este informe** |
| hoy | **OGameX** | lanedirt | Hecho desde cero con Laravel 12; copia el OGame de antes de la expansión "Formas de vida" |

**Cuidado con dos nombres que confunden:**
- En PyPI hay un paquete llamado "xnova" que describe un juego para móviles inspirado en OGame (React Native, Node.js, PostgreSQL). Es otro proyecto, en etapa temprana y sin relación con la línea de arriba.
- Existe una "XNova" rusa (xnova.su). No se pudo comprobar si sigue abierta ni qué versión usa.

## OGame hoy (el original con el que todos comparan)

- **Sigue abierto**, operado por Gameforge, con universos nuevos cada tanto y premios de temporada por entrar a ellos.
- **App para móviles** desde 2022 (por su 20 aniversario). La versión de la tienda se actualizó por última vez en julio de 2026; su nota es baja (2,67 de 5, con pocas reseñas).
- **Clases** (desde 2019): tres clases de jugador, una para producir, otra para pelear y otra para investigar, cada una con una nave propia.
- **Formas de vida** (2022): cuatro especies (Humanos, Rock'tal, Mechas y Kaelesh), con 48 edificios y 72 tecnologías nuevas. Agregan población y comida como recursos; no se pueden robar, pero sí destruir en un ataque.
- **Logros y avatares** (2024, por su 22 aniversario): logros, avatares, títulos, aspectos de planeta y un ranking de logros.
- **Jugadores:** Gameforge habla de más de 100 millones de registrados en su historia. Son registros, no jugadores activos; no se encontró una cifra de activos.

**Qué significa:** Xnova es la versión **más simple** de la familia. Es el OGame de alrededor de 2008: sin clases, sin formas de vida y sin logros. Si alguien jugó Xnova, jugó el OGame clásico.

## Lo que dejan claro las licencias

- El código de Xnova y el de XG Proyect son **GPL 3**: si se copia ese código, lo que se construya con él también tiene que publicarse con GPL 3. 2Moons y SteemNova son **MIT**, que solo pide mantener el aviso de autor. Leer sus reglas y sus números como referencia no obliga a nada de eso.
- OGameX aclara en su página que **el arte y la interfaz son de Gameforge**. Las reglas pasan de un juego a otro en toda la familia, pero los nombres propios, los textos y las imágenes no deberían copiarse.
- Esto es lo que dicen los propios proyectos, no un consejo legal.

## Fuentes

- Créditos de 2Moons (línea UGamela → XNova → XGP → 2Moons, con años y autores): [README de 2Moons](https://github.com/jkroepke/2Moons)
- Código leído: [xmke/xnova en GitHub](https://www.github.com/xmke/xnova) (archivado el 29-ene-2023, GPL 3)
- XNova:Legacies y Next-Gen: [wiki de XNova:Legacies](https://absinthe.tuxfamily.org/xnlegacies/statique/wiki/cache/3/3739c5a139968213ed452e1d4cf55d4a.xhtml), [Open Hub](https://openhub.net/p/xnova), [SourceForge](https://www.sourceforge.net/directory/?q=xnova)
- UGamela: [proyecto ugml](https://identichosting.duckdns.org/ugml/php-client)
- XG Proyect: [versión 3 (aviso de cambio a la 4)](https://github.com/XGProyect/XG-Proyect-v3.x.x), [versión 4](https://github.com/XGProyect/XGProyect), [traducciones](https://github.com/BeReal86/XG-Proyect-v3.x.x-Languages), [perfil de Lucas Kovacs](https://www.github.com/LucasKovacs)
- 2Moons: [ModDB](https://www.moddb.com/engines/2moons), [licencia MIT](https://github.com/jkroepke/2Moons)
- SteemNova: [premios diarios por alianza (2020)](https://steemit.steemapps.com/steemnova/@steemnova/steemnova-classic---2020-03-13-daily-alliance-shares-and-player-rewards), [propuesta de SteemNova 2 (unos 350 activos)](https://steemit.steemapps.com/intintedao/@intinte/come-steemnova-2), [código](https://gitee.com/sbdx/steemnova)
- OGameX: [README](https://www.light55.lima-city.de/OgameX/README.md), [ficha](https://awesome.ecosyste.ms/projects/github.com%2Flanedirt%2Fogamex)
- Historia de OGame: [OGame Wiki](https://ogame.fandom.com/wiki/History_Of_OGame)
- OGame hoy: [Formas de vida](https://uberstrategist.com/press-release/lifeforms-expansion-release), [22 aniversario](https://www.gamedeveloper.com/press-release/achievements-and-avatars-in-ogame-mega-update-announced-for-the-space-strategy-classic-s-22nd-anniversary), [app móvil](https://www.pocketgamer.com/ogame/out-now/), [ficha de la app](https://www.appbrain.com/appstore/ogame/ios-1593395507)
- Paquete "xnova" para móviles (otro proyecto): [PyPI](https://pypi.org/project/xnova/)
