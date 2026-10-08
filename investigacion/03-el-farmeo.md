# 3 · El farmeo: el corazón del juego

> **Investigación** · [Volver al índice](README.md)

En Xnova, como en toda la familia de OGame, **casi todo es farmear**: juntar recursos para crecer más rápido que los demás. Hay cuatro formas de hacerlo, y cada jugador las mezcla a su gusto.

| Forma | Qué hace el jugador | Riesgo |
|---|---|---|
| **Farmear tus minas** | Sube minas, gasta lo que producen en más minas, y vuelve a empezar | Si no entra a gastar, otro se lo roba |
| **Farmear a otros (saquear)** | Espía planetas, sobre todo de **inactivos**, y los ataca para llevarse la mitad de sus recursos | Gastar combustible para nada, o caer en una trampa |
| **Farmear escombros** | Recoge con recicladores lo que queda flotando después de una batalla, propia o ajena | Que otro llegue primero |
| **Farmear expediciones** | Manda flotas al espacio profundo a ver qué encuentran | Perder naves (en Xnova, 1 de cada 11 veces se pierde toda la flota) |

---

## 1. El saqueo, paso a paso

1. **Buscar.** En la vista de galaxia se ve quién vive en cada sistema. Los jugadores marcados **(i)** llevan 7 días sin entrar y los **(I)**, 28. Un inactivo sigue produciendo con sus minas y nadie gasta lo que junta: es la presa más segura. Se empieza por los sistemas cercanos, porque el viaje es más corto y gasta menos combustible.
2. **Espiar.** Se mandan sondas. El informe muestra recursos, flota, defensas, edificios e investigaciones, según la diferencia de nivel de Espionaje (ver [Reglas §11](02-reglas-y-numeros.md#11-espionaje)). Sin espiar, se puede llegar a un planeta vacío o a uno lleno de defensas.
3. **Calcular.** Cuánto se puede llevar y cuántas naves de carga hacen falta. Se mira la actividad del otro: si estuvo conectado hace 5 minutos, puede haber escondido todo o estar esperando.
4. **Atacar.** Se manda la flota: naves de carga solas si no hay defensas, o con naves de guerra si las hay.
5. **Reciclar.** Si hubo naves destruidas, se mandan recicladores a recoger los escombros.
6. **Repetir.** Los mejores jugadores llevan una **lista de granjas**: decenas de planetas inactivos que atacan por turno, dándoles tiempo a que vuelvan a juntar recursos.

### Un ejemplo con los números de Xnova

Un inactivo con minas de nivel 15 (metal), 12 (cristal) y 10 (deuterio) tiene guardados **100.000 de metal, 60.000 de cristal y 20.000 de deuterio**.

- **Lo máximo que se puede robar** es la mitad: 50.000 + 30.000 + 10.000 = **90.000**.
- **Cuántas naves grandes de carga hacen falta.** Como Xnova llena la bodega en orden (metal hasta un tercio, luego cristal, luego deuterio) y no vuelve a llenar lo que sobra, hace falta más bodega que lo que se roba:

| Naves grandes de carga | Bodega | Se lleva | Total |
|---|---|---|---|
| 3 | 75.000 | 25.000 M, 25.000 C, 10.000 D | 60.000 |
| 4 | 100.000 | 33.333 M, 30.000 C, 10.000 D | 73.333 |
| 5 | 125.000 | 41.667 M, 30.000 C, 10.000 D | 81.667 |
| **6** | **150.000** | 50.000 M, 30.000 C, 10.000 D | **90.000** |

- **El viaje** (10 sistemas de distancia, Motor de combustión 6):

| Velocidad elegida | Duración de la ida | Deuterio que gasta |
|---|---|---|
| 100 % | 1 h 42 min | 126 |
| 50 % | 3 h 24 min | 71 |
| 10 % | 17 horas | 39 |

- **Cuánto se recupera la granja:** con esas minas, el inactivo produce unos **1.900 de metal, 760 de cristal y 310 de deuterio por hora**. En un día vuelve a tener unos 70.000 para robar.

**La cuenta que hace un saqueador:** ganancia = botín + escombros recogidos − combustible − naves perdidas. Contra un inactivo sin defensas, el ataque casi siempre gana. Contra un planeta con defensas, en Xnova casi nunca conviene: **las defensas no dejan escombros** (por el error del código) y se reconstruyen entre el 60 % y el 80 % solas.

---

## 2. Los estilos de jugador que nacen del farmeo

| Estilo | Cómo juega | Qué premia Xnova |
|---|---|---|
| **Minero** | Sube minas, gasta todo antes de desconectarse, esconde la flota | Experiencia de minero → oficiales de la rama minera (Geólogo, Ingeniero, Constructor...) |
| **Saqueador** | Vive de robar: flota de carga, sondas y listas de granjas | Experiencia de saqueador (+1 por ataque) → oficiales militares (Almirante, Comandante, General...) |
| **Tortuga** | Llena el planeta de defensas para que atacarlo no rinda | Las defensas se reconstruyen y no dejan escombros |
| **Cazador de flotas** | Busca flotas ajenas para destruirlas y reciclar sus escombros (en inglés, *fleet crashing*) | En Xnova, el 60 % de las naves destruidas queda como escombros |

---

## 3. Cómo se defiende el que es farmeado

| Defensa | Cómo funciona |
|---|---|
| **Gastar antes de irse** | Lo que se gasta en construcciones no se puede robar. La regla de oro es no dejar recursos acumulados |
| **Esconder la flota** (en inglés, *fleet save*) | Antes de desconectarse, se manda la flota de viaje lento (al 10 %) a otro planeta propio, a una luna o a un inactivo, para que no esté en casa cuando llegue el ataque. Si se manda como transporte, se lleva también los recursos |
| **Defensas** | Hacen que el ataque no sea rentable |
| **Luna y sensor phalanx** | Para ver quién viene y cuándo |
| **Alianza** | Los aliados pueden mandar su flota a defender (misión "mantener posición") |
| **Modo vacaciones** | Nadie te puede atacar, pero tampoco produces. En Xnova dura como mínimo 24 horas |

**El problema:** todas estas defensas piden **estar conectado en el momento justo**. Ver [Lo que enganchaba y lo que espantaba](04-lo-que-enganchaba-y-lo-que-espantaba.md).

---

## 4. Las reglas que frenan el farmeo

| Regla | Qué evita | En Xnova | En OGame |
|---|---|---|---|
| **Protección de novatos** | Que un grande se coma a un recién llegado | No se puede atacar a quien tiene 5 veces menos puntos | 1 a 5 hasta 50.000 puntos y 1 a 10 hasta 500.000 (universos nuevos). El inactivo la pierde |
| **Límite de ataques** | Que se ataque sin parar al mismo planeta | No existe en el código | 6 ataques al mismo planeta o luna cada 24 horas; se castiga a quien lo rompe |
| **Botín de la mitad** | Que un ataque deje al otro en cero | 50 % | 50 % en las reglas clásicas |
| **Reconstrucción de defensas** | Que la tortuga pierda todo | 60 % a 80 % | Alrededor de 70 % |
| **Inactivos atacables** | Que los que dejaron el juego queden fuera del farmeo | Sí | Sí, de forma expresa |
| **Modo vacaciones** | Que un viaje o una semana ocupada te arruine la cuenta | Mínimo 24 horas | Mínimo 48 horas |

---

## 5. Lo que se siente ser la granja

Testimonios de jugadores de OGame (son anécdotas, no estadísticas):

- Un jugador perdió toda su flota **por no poder entrar un día**, por trabajo o familia.
- Otro cuenta que, a mitad de partida, los jugadores más fuertes lo atacaron **durante días hasta dejarle solo las investigaciones**.
- Un jugador ponía **alarmas de madrugada**, incluso en días de trabajo, para esconder la flota antes de volver a dormir. Otro dejó el juego por el costo de esa rutina.
- Un consejo viejo de foro resume la otra cara: si escondes bien la flota y no armas una flota grande demasiado pronto, casi nadie te ataca, porque **la mayoría ataca para ganar, no por gusto**.

**En resumen:** el farmeo es la parte más divertida para el que saquea y la más dolorosa para el saqueado. Los inactivos son lo que equilibra eso: dan de comer a los saqueadores sin que sufra un jugador activo.

---

## Fuentes

- Números del ejemplo: código de Xnova ([xmke/xnova](https://www.github.com/xmke/xnova)), fórmulas en [Reglas y números](02-reglas-y-numeros.md)
- Farmeo de inactivos, espionaje y riesgos: [hilo de OGame en AnandTech](https://forums.anandtech.com/threads/browser-based-game-ogame-come-on-join.1807982/page-20), [mensaje 19335031](https://forums.anandtech.com/threads/browser-based-game-ogame-come-on-join.1807982/post-19335031), [mensaje 19313734](https://forums.anandtech.com/threads/browser-based-game-ogame-come-on-join.1807982/post-19313734), [mensaje 19318129](https://forums.anandtech.com/threads/browser-based-game-ogame-come-on-join.1807982/post-19318129)
- Esconder la flota (guía de un juego de la misma familia): [Fleet / Resource Saving](https://playsfc2.com/wiki/fleet-saving)
- Bot de farmeo automático para OGameX (muestra el ciclo buscar → espiar → atacar): [ogamebot](https://awesome.ecosyste.ms/projects/github.com%2Fhalfguru%2Fogamebot)
- Reglas: [Reglas de OGame según Gameforge](https://gameforge.com/en-GB/games/ogame-rules.html), [OGame Wiki: Bashing](https://ogame.fandom.com/wiki/Bashing?oldid=8494), [OGame Wiki: inactivos](https://ogame.fandom.com/wiki/Inactive_Players)
- Testimonios: [reseñas en Trustpilot (ogame.dk)](https://uk.trustpilot.com/review/www.ogame.dk), [reseñas en Trustpilot (ogame.de)](https://uk.trustpilot.com/review/ogame.de), [foro de Overclockers](https://forums.overclockers.co.uk/threads/ogame.18529944), [hilo de OGame en Overclockers](https://forums.overclockers.co.uk/goto/post?id=9917897)
