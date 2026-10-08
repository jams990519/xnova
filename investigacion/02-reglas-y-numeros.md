# 2 · Las reglas de Xnova, con sus números

> **Investigación** · [Volver al índice](README.md)

**De dónde salen los números:** del código de XNova:Legacies ([xmke/xnova](https://www.github.com/xmke/xnova)), leído archivo por archivo: precios (`includes/data/prices.php`), combate (`combat.php`), requisitos (`requirements.php`), producción (`production.php`), la batalla (`includes/ataki.php`), las misiones (`includes/functions/MissionCase*.php`), los vuelos (`includes/unlocalised.php`) y la configuración inicial (`includes/databaseinfos.php`). Cuando OGame clásico hace algo distinto, se dice.

**Los nombres** son los de la versión en español de OGame. El número de cada cosa (ID) es el mismo en toda la familia: 1 a 44 edificios, 106 a 199 investigaciones, 202 a 216 naves, 401 a 503 defensas y misiles, 601 a 615 oficiales.

---

## 1. El universo

| Qué | Valor en Xnova |
|---|---|
| Tamaño | **9 galaxias × 499 sistemas × 15 posiciones = 67.365 lugares**. En cada lugar puede haber un planeta, una luna y un campo de escombros |
| Planeta inicial | **163 campos**. Cada nivel de cada edificio ocupa un campo |
| Velocidad de la economía | `game_speed = 2500`, que equivale a ×1 |
| Velocidad de las flotas | `fleet_speed = 2500`, que equivale a ×1 |
| Multiplicador de recursos | ×1 |
| Colonias por jugador | Límite en el código: **9.000**, o sea, sin límite real. En OGame la investigación de Astrofísica limita cuántas colonias tienes |
| Flotas en vuelo a la vez | **1 + nivel de Computación** |

**El tamaño y la temperatura dependen de la posición** (qué tan cerca del sol está el planeta):

| Posición | Temperatura mínima (al azar) | Campos aproximados (al azar) |
|---|---|---|
| 1 a 3 | 0 a 100 °C | 40 a 95 (pequeños) |
| 4 a 6 | −25 a 75 °C | 80 a 240 (los más grandes) |
| 7 a 9 | −50 a 50 °C | 115 a 190 |
| 10 a 12 | −75 a 25 °C | 75 a 130 |
| 13 a 15 | −100 a 10 °C | 40 a 300 (muy variables) |

La temperatura máxima es siempre la mínima + 40. A los campos se les suma o resta un extra al azar de hasta ±110. **Por qué importa:** los planetas calientes dan más energía con satélites solares; los fríos dan más deuterio.

## 2. Los recursos

| Recurso | Para qué sirve | Se puede robar |
|---|---|---|
| **Metal** | Lo más barato y lo que más se gasta | Sí |
| **Cristal** | Electrónica e investigación | Sí |
| **Deuterio** | Combustible de las flotas y tecnologías avanzadas | Sí |
| **Energía** | Hace funcionar las minas. No se acumula: se produce y se consume a cada momento | No |

**Ingreso gratis:** cada planeta da **20 de metal y 10 de cristal por hora** aunque no tenga minas.

**Producción por hora** (N = nivel; todo × 0,1 × el porcentaje de producción elegido, de 0 % a 100 % en pasos de 10 %):

| Edificio | Produce | Consume |
|---|---|---|
| Mina de metal | 30 · N · 1,1^N de metal | 10 · N · 1,1^N de energía |
| Mina de cristal | 20 · N · 1,1^N de cristal | 10 · N · 1,1^N de energía |
| Sintetizador de deuterio | 10 · N · 1,1^N · (1,28 − 0,002 · temperatura máxima) de deuterio | **30** · N · 1,1^N de energía (en OGame, 20) |
| Planta de energía solar | 20 · N · 1,1^N de energía | — |
| Planta de fusión | **50** · N · 1,1^N de energía (en OGame es menos) | 10 · N · 1,1^N de deuterio |
| Satélite solar (cada uno) | (temperatura máxima / 4 + 20) de energía | — |

**Si falta energía,** todas las minas bajan su producción en la misma proporción. Ejemplo: con 80 % de la energía que piden, producen el 80 %.

**Ejemplos** (temperatura máxima 40 °C, producción al 100 %; las columnas de metal y cristal ya suman el ingreso gratis):

| Nivel | Metal/hora | Cristal/hora | Deuterio/hora | Energía que pide la mina de metal | Energía que da la planta solar |
|---|---|---|---|---|---|
| 1 | 53 | 32 | 13 | 11 | 22 |
| 5 | 262 | 171 | 97 | 81 | 161 |
| 10 | 798 | 529 | 311 | 259 | 519 |
| 15 | 1.900 | 1.263 | 752 | 627 | 1.253 |
| 20 | 4.056 | 2.701 | 1.615 | 1.345 | 2.691 |
| 25 | 8.146 | 5.427 | 3.250 | 2.709 | 5.417 |
| 30 | 15.724 | 10.480 | 6.282 | 5.235 | 10.470 |

**Almacenes:** en Xnova cada almacén guarda **10.000.000 × 1,5^nivel**. Es enorme: en la práctica el almacén casi no limita. (En OGame clásico la base es 100.000, así que allá sí hay que subirlos.)

## 3. Edificios

**Costo del siguiente nivel = costo base × (factor ^ nivel actual).** Ejemplo: la mina de metal nivel 10 cuesta 60 × 1,5^9 ≈ 2.306 de metal y 576 de cristal.

| ID | Edificio | Metal | Cristal | Deuterio | Sube ×nivel | Requisitos |
|---|---|---|---|---|---|---|
| 1 | Mina de metal | 60 | 15 | 0 | 1,5 | — |
| 2 | Mina de cristal | 48 | 24 | 0 | 1,6 | — |
| 3 | Sintetizador de deuterio | 225 | 75 | 0 | 1,5 | — |
| 4 | Planta de energía solar | 75 | 30 | 0 | 1,5 | — |
| 12 | Planta de fusión | 900 | 360 | 180 | 1,8 | Sintetizador de deuterio 5, Energía 3 |
| 14 | Fábrica de robots | 400 | 120 | 200 | 2 | — |
| 15 | Fábrica de nanobots | 1.000.000 | 500.000 | 100.000 | 2 | Fábrica de robots 10, Computación 10 |
| 21 | Hangar | 400 | 200 | 100 | 2 | Fábrica de robots 2 |
| 22 | Almacén de metal | 2.000 | 0 | 0 | 2 | — |
| 23 | Almacén de cristal | 2.000 | 1.000 | 0 | 2 | — |
| 24 | Contenedor de deuterio | 2.000 | 2.000 | 0 | 2 | — |
| 31 | Laboratorio | 200 | 400 | 200 | 2 | — |
| 33 | Terraformador | 0 | 50.000 | 100.000 (+1.000 de energía) | 2 | Fábrica de nanobots 1, Energía 12 |
| 34 | Depósito de alianza | 20.000 | 40.000 | 0 | 2 | — |
| 41 | Base lunar (solo en lunas) | 20.000 | 40.000 | 20.000 | 2 | — |
| 42 | Sensor phalanx (solo en lunas) | 20.000 | 40.000 | 20.000 | 2 | Base lunar 1 |
| 43 | Salto cuántico (solo en lunas) | 2.000.000 | 4.000.000 | 2.000.000 | 2 | Base lunar 1, Hiperespacio 7 |
| 44 | Silo de misiles | 20.000 | 20.000 | 1.000 | 2 | — |

**Para qué sirve cada uno:**
- **Fábrica de robots** y **de nanobots:** construyen más rápido (ver §5). Los nanobots parten el tiempo a la mitad por cada nivel.
- **Hangar:** construye naves y defensas; su nivel desbloquea naves y acelera su construcción.
- **Laboratorio:** investiga; su nivel desbloquea investigaciones y las acelera.
- **Terraformador:** agrega campos al planeta.
- **Depósito de alianza:** da combustible a las flotas aliadas que se quedan a defender tu planeta.
- **Base lunar:** agrega campos a la luna (las lunas casi no tienen).
- **Sensor phalanx:** desde la luna, deja ver las flotas que van y vienen de planetas cercanos.
- **Salto cuántico:** mueve flotas al instante de una luna a otra.
- **Silo de misiles:** guarda misiles de intercepción e interplanetarios.

## 4. Investigaciones

Todas las investigaciones son **del jugador**, no del planeta: valen en todos sus planetas.

| ID | Investigación | Metal | Cristal | Deuterio | Sube ×nivel | Requisitos |
|---|---|---|---|---|---|---|
| 106 | Espionaje | 200 | 1.000 | 200 | 2 | Laboratorio 3 |
| 108 | Computación | 0 | 400 | 600 | 2 | Laboratorio 1 |
| 109 | Militar (armas) | 800 | 200 | 0 | 2 | Laboratorio 4 |
| 110 | Defensa | 200 | 600 | 0 | 2 | Energía 3, Laboratorio 6 |
| 111 | Blindaje | 1.000 | 0 | 0 | 2 | Laboratorio 2 |
| 113 | Energía | 0 | 800 | 400 | 2 | Laboratorio 1 |
| 114 | Hiperespacio | 0 | 4.000 | 2.000 | 2 | Energía 5, Defensa 5, Laboratorio 7 |
| 115 | Motor de combustión | 400 | 0 | 600 | 2 | Energía 1, Laboratorio 1 |
| 117 | Motor de impulso | 2.000 | 4.000 | 600 | 2 | Energía 1, Laboratorio 2 |
| 118 | Propulsor hiperespacial | 10.000 | 20.000 | 6.000 | 2 | Hiperespacio 3, Laboratorio 7 |
| 120 | Láser | 200 | 100 | 0 | 2 | Laboratorio 1, Energía 2 |
| 121 | Iónica | 1.000 | 300 | 100 | 2 | Laboratorio 4, Láser 5, Energía 4 |
| 122 | Plasma | 2.000 | 4.000 | 1.000 | 2 | Laboratorio 5, Energía 8, Láser 10, Iónica 5 |
| 123 | Red de investigación intergaláctica | 240.000 | 400.000 | 160.000 | 2 | Laboratorio 10, Computación 8, Hiperespacio 8 |
| 124 | Expediciones (en OGame, Astrofísica) | 4.000 | 8.000 | 4.000 | 2 | Laboratorio 3, Computación 4, Motor de impulso 3 |
| 199 | Gravitón | — | — | — (pide 300.000 de energía) | 3 | Laboratorio 12 |

**Qué hace cada una:**
- **Militar:** +10 % de ataque por nivel a naves y defensas.
- **Defensa (110) y Blindaje (111):** en OGame, Defensa sube los escudos y Blindaje sube el casco, +10 % por nivel. **En el combate de Xnova están cruzadas:** Blindaje sube los escudos, y Defensa solo cambia el número que se muestra, porque las bajas se calculan con el casco base (ver §16).
- **Espionaje:** informes más completos y menos probabilidad de que te descubran las sondas (ver §11).
- **Computación:** +1 flota en vuelo a la vez por nivel.
- **Motores:** suben la velocidad de las naves. Combustión +10 % por nivel, impulso +20 %, propulsor hiperespacial +30 % (ver §8).
- **Red intergaláctica:** cada nivel suma un laboratorio de otro planeta a la investigación (se suman los mejores).
- **Gravitón:** solo sirve para la Estrella de la muerte. No cuesta recursos sino 300.000 de energía de un solo planeta (normalmente con miles de satélites solares).

## 5. Tiempos de construcción

| Qué | Horas | Oficial que lo acelera |
|---|---|---|
| Edificio | (metal + cristal) / (2.500 × (1 + fábrica de robots)) × 0,5^nanobots | Constructor: −10 % por nivel |
| Investigación | (metal + cristal) / (2.500 × 2 × (1 + laboratorio)) | Científico: −10 % por nivel |
| Nave o defensa (cada una) | (metal + cristal) / (2.500 × (1 + hangar)) × 0,5^nanobots | Defensor: −37,5 % por nivel en defensas; Tecnócrata: −5 % por nivel en naves (según su descripción) |

**Ojo:** en OGame clásico la investigación divide entre 1.000, no entre 5.000. En Xnova **se investiga unas 5 veces más rápido**.

**Ejemplo: mina de metal** (sin oficiales, sin nanobots):

| Nivel | Metal | Cristal | Tiempo sin robots | Tiempo con robots 10 |
|---|---|---|---|---|
| 5 | 303 | 75 | 9 minutos | 1 minuto |
| 10 | 2.306 | 576 | 1,2 horas | 6 minutos |
| 15 | 17.515 | 4.378 | 8,8 horas | 48 minutos |
| 20 | 133.010 | 33.252 | 2,8 días | 6 horas |
| 25 | 1.010.046 | 252.511 | 21 días | 1,9 días |
| 30 | 7.670.042 | 1.917.510 | 160 días | 14,5 días |

**Qué enseña la tabla:** el costo crece en forma exponencial. Los primeros niveles salen en minutos y los últimos en semanas. Esa curva es la que hace que el juego dure meses.

## 6. Naves

**Casco = (metal + cristal) / 10.** Cuando hay dos valores de velocidad o consumo, el segundo se usa al mejorar el motor (ver §8).

| ID | Nave | Metal | Cristal | Deut. | Casco | Escudo | Ataque | Velocidad | Carga | Consumo | Requisitos |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 202 | Nave pequeña de carga | 2.000 | 2.000 | 0 | 400 | 10 | 5 | 5.000 → 10.000 | 5.000 | 20 → 40 | Hangar 2, Motor de combustión 2 |
| 203 | Nave grande de carga | 6.000 | 6.000 | 0 | 1.200 | 25 | 5 | 7.500 | 25.000 | 50 | Hangar 4, Motor de combustión 6 |
| 204 | Cazador ligero | 3.000 | 1.000 | 0 | 400 | 10 | 50 | 12.500 | 50 | 20 | Hangar 1, Motor de combustión 1 |
| 205 | Cazador pesado | 6.000 | 4.000 | 0 | 1.000 | 25 | 150 | 10.000 | 100 | 75 | Hangar 3, Blindaje 2, Motor de impulso 2 |
| 206 | Crucero | 20.000 | 7.000 | 2.000 | 2.700 | 50 | 400 | 15.000 | 800 | 300 | Hangar 5, Motor de impulso 4, Iónica 2 |
| 207 | Nave de batalla | 45.000 | 15.000 | 0 | 6.000 | 200 | 1.000 | 10.000 | 1.500 | 500 | Hangar 7, Propulsor hiperespacial 4 |
| 208 | Colonizador | 10.000 | 20.000 | 10.000 | 3.000 | 100 | 50 | 2.500 | 7.500 | 1.000 | Hangar 4, Motor de impulso 3 |
| 209 | Reciclador | 10.000 | 6.000 | 2.000 | 1.600 | 10 | 1 | 2.000 | 20.000 | 300 | Hangar 4, Motor de combustión 6, Defensa 2 |
| 210 | Sonda de espionaje | 0 | 1.000 | 0 | 100 | 0 | 0 | 100.000.000 | 5 | 1 | Hangar 3, Motor de combustión 3, Espionaje 2 |
| 211 | Bombardero | 50.000 | 25.000 | 15.000 | 7.500 | 500 | 1.000 | 4.000 → 5.000 | 500 | 1.000 | Motor de impulso 6, Hangar 8, Plasma 5 |
| 212 | Satélite solar | 0 | 2.000 | 500 | 200 | 10 | 1 | 0 | 0 | 0 | Hangar 1 |
| 213 | Destructor | 60.000 | 50.000 | 15.000 | 11.000 | 500 | 2.000 | 5.000 | 2.000 | 1.000 | Hangar 9, Propulsor hiperespacial 6, Hiperespacio 5 |
| 214 | Estrella de la muerte | 5.000.000 | 4.000.000 | 1.000.000 | 900.000 | 50.000 | 200.000 | 100 | 1.000.000 | 1 | Hangar 12, Propulsor hiperespacial 7, Hiperespacio 6, Gravitón 1 |
| 215 | Acorazado | 30.000 | 40.000 | 15.000 | 7.000 | 400 | 700 | 10.000 | 750 | 250 | Hiperespacio 5, Láser 12, Propulsor hiperespacial 5, Hangar 8 |
| 216 | **Supernova** (solo Xnova) | 150.000.000 | 300.000.000 | 450.000.000 (+1.000.000.000 de energía) | 45.000.000 | 400 | 700 | 1.000 | 1.000.000 | 100.000 | Hangar 25, Propulsor hiperespacial 18, Hiperespacio 14, Gravitón 3, y el oficial Saqueador (según su descripción) |

**Para qué sirve cada una, en pocas palabras:** las de carga llevan el botín; los cazadores son la flota barata del principio; crucero, nave de batalla, acorazado, bombardero y destructor son la flota de guerra; el **reciclador** recoge escombros; la **sonda** espía; el **colonizador** funda colonias; el **satélite** da energía y no vuela; la **Estrella de la muerte** destruye flotas enteras y puede destruir lunas.

**La Supernova parece a medio terminar:** cuesta casi mil millones de recursos, sus escudos y su ataque son una copia de los del acorazado, y en la tabla de producción figura gastando energía.

## 7. Defensas y misiles

Las defensas no se mueven: solo protegen el planeta donde están.

| ID | Defensa | Metal | Cristal | Deut. | Casco | Escudo | Ataque | Requisitos |
|---|---|---|---|---|---|---|---|---|
| 401 | Lanzamisiles | 2.000 | 0 | 0 | 200 | 20 | 80 | Hangar 1 |
| 402 | Láser pequeño | 1.500 | 500 | 0 | 200 | 25 | 100 | Energía 1, Hangar 2, Láser 3 |
| 403 | Láser grande | 6.000 | 2.000 | 0 | 800 | 100 | 250 | Energía 3, Hangar 4, Láser 6 |
| 404 | Cañón gauss | 20.000 | 15.000 | 2.000 | 3.500 | 200 | 1.100 | Hangar 6, Energía 6, Militar 3, Defensa 1 |
| 405 | Cañón iónico | 2.000 | 6.000 | 0 | 800 | 500 | 150 | Hangar 4, Iónica 4 |
| 406 | Cañón de plasma | 50.000 | 50.000 | 30.000 | 10.000 | 300 | 3.000 | Hangar 8, Plasma 7 |
| 407 | Cúpula pequeña de protección | 10.000 | 10.000 | 0 | 2.000 | 2.000 | 1 | Defensa 2, Hangar 1 |
| 408 | Cúpula grande de protección | 50.000 | 50.000 | 0 | 10.000 | 2.000 | 1 | Defensa 6, Hangar 6 |
| 502 | Misil de intercepción | 8.000 | 2.000 | 0 | 1.000 | 1 | 1 | Silo de misiles 2 |
| 503 | Misil interplanetario | 12.500 | 2.500 | 10.000 | 1.500 | 1 | 12.000 | Silo de misiles 4 |

- **Después de una batalla,** se reconstruye sola entre el **60 % y el 80 %** de la defensa destruida (en OGame, alrededor del 70 %).
- **Misil interplanetario:** se lanza contra las defensas de otro planeta sin mandar flota. **El de intercepción** destruye misiles que vienen hacia ti.

## 8. Viajar: distancia, duración y combustible

**Distancia:**

| Viaje | Distancia |
|---|---|
| A otra galaxia | 20.000 × diferencia de galaxias |
| A otro sistema de la misma galaxia | 2.700 + 95 × diferencia de sistemas |
| A otro planeta del mismo sistema | 1.000 + 5 × diferencia de posiciones |
| Del planeta a su luna, o al revés | 5 |

**Velocidad de cada nave:** su velocidad base × (1 + bono del motor × nivel del motor). La flota entera va a la velocidad de **su nave más lenta**. Dos casos raros: cuando la nave pequeña de carga y el bombardero cambian de motor, el bono se sigue calculando sobre su velocidad vieja (5.000 y 4.000) y se suma a la nueva (10.000 y 5.000).

| Motor | Bono por nivel | Naves |
|---|---|---|
| Combustión | +10 % | Nave grande de carga, cazador ligero, reciclador, sonda, nave pequeña de carga (hasta impulso 4) |
| Impulso | +20 % | Cazador pesado, crucero, colonizador; la nave pequeña de carga desde impulso 5 (con base 10.000); el bombardero hasta propulsor hiperespacial 7 |
| Propulsor hiperespacial | +30 % | Nave de batalla, destructor, Estrella de la muerte, acorazado, Supernova; el bombardero desde nivel 8 (con base 5.000) |

**Duración del viaje (en segundos)** = (35.000 / velocidad elegida × √(distancia × 10 / velocidad de la flota) + 10) / velocidad del universo. La velocidad elegida va de 10 % a 100 %, en pasos de 10 %.

**Combustible (deuterio)** = suma, por cada tipo de nave, de consumo × cantidad × distancia / 35.000 × (v / 10 + 1)², donde v sale de la velocidad elegida; más 1. **En pocas palabras:** ir más lento gasta mucho menos combustible. Por eso los jugadores mandan flotas al 10 % para ahorrar o para esconderlas (ver [El farmeo](03-el-farmeo.md)).

## 9. La batalla

Xnova usa un combate **más simple que OGame**: no simula nave por nave, sino **por grupos**.

1. Hay **hasta 7 rondas** (OGame usa 6). Se para antes si un lado se queda sin nada.
2. En cada ronda, cada lado suma su **ataque total**: cantidad × ataque × (1 + 0,1 × Militar + 0,05 × Almirante) × un azar entre **0,8 y 1,2**.
3. Ese ataque se reparte entre los grupos enemigos **según cuántas unidades tiene cada grupo**.
4. El **escudo** de cada grupo (cantidad × escudo × mejoras × un azar entre 0,8 y 1,2) se come primero el daño. Lo que sobra mata unidades, a razón de una por cada (metal + cristal) / 10 de daño.
5. **Fuego rápido:** en cada ronda, cada tipo de nave que tiene fuego rápido contra otro tipo le quita además entre el 50 % y el 100 % de ese número de unidades. **Ojo:** el número no se multiplica por cuántas naves disparan. Una sola Estrella de la muerte o cien quitan lo mismo: entre 125 y 250 naves pequeñas de carga por ronda.
6. **Resultado:** gana el atacante si el defensor se queda sin nada; gana el defensor si el atacante se queda sin nada; si quedan los dos (o ninguno), es **empate**.

**Fuego rápido** (solo los valores mayores que 1, sin contar sondas y satélites: casi todas las naves tienen 5 contra ellos):

| Quién dispara | Contra quién (valor) |
|---|---|
| Cazador ligero | Nave pequeña de carga 2 |
| Cazador pesado | Nave pequeña de carga 3 |
| Crucero | Cazador ligero 6, Lanzamisiles 10 |
| Nave de batalla | Lanzamisiles 8 |
| Bombardero | Lanzamisiles 20, Láser pequeño 20, Láser grande 10, Cañón iónico 10 |
| Destructor | Acorazado 2, Láser pequeño 10 |
| Estrella de la muerte | Nave pequeña de carga 250, Nave grande de carga 250, Cazador ligero 200, Cazador pesado 100, Crucero 33, Nave de batalla 30, Colonizador 250, Reciclador 250, Bombardero 25, Destructor 5, Acorazado 15, Lanzamisiles 200, Láser pequeño 200, Láser grande 100, Cañón gauss 50, Cañón iónico 100 |
| Acorazado | Nave pequeña de carga 3, Nave grande de carga 3, Cazador pesado 4, Crucero 4, Nave de batalla 7 |
| Supernova | 5 veces lo de la Estrella de la muerte (por ejemplo, 1.250 naves pequeñas de carga), y además Estrella de la muerte 5 y Cañón de plasma 5 |

**Cómo funciona en OGame (para comparar):** cada nave dispara por separado a un blanco al azar; si el disparo no llega al 1 % del escudo, se pierde; una nave con el casco por debajo del 70 % puede explotar; y el fuego rápido da una probabilidad de volver a disparar. Es más justo, pero mucho más pesado de calcular.

## 10. Botín, escombros y lunas

**Botín** (solo si gana el atacante):
- Se puede llevar **la mitad** de cada recurso del planeta.
- Se carga en orden: **metal** hasta un tercio de la bodega; **cristal** hasta la mitad de lo que queda; **deuterio** con el resto.
- La bodega es la suma de la carga de las naves que sobrevivieron.

**Escombros:**
- La configuración dice **30 % de las naves** y **30 % de las defensas** destruidas (metal y cristal; el deuterio no deja escombros).
- **Pero por un error del código,** las dos cuentas usan las naves: en la práctica quedan como escombros el **60 % de las naves** destruidas y **nada de las defensas** (ver §16).
- Los escombros quedan flotando en ese lugar del mapa hasta que alguien los recoge con **recicladores** (20.000 de carga cada uno).

**Lunas:**
- Si una batalla deja **100.000 o más** de escombros, hay probabilidad de que nazca una luna: **1 % por cada 100.000**, con un tope de **20 %** (desde 2.000.000).
- Solo puede haber una luna por planeta.
- Las lunas sirven para el sensor phalanx, el salto cuántico y para esconder flotas.

## 11. Espionaje

- Mandas **sondas** a un planeta y vuelve un informe.
- **Qué tan completo sale el informe** depende de la diferencia entre tu nivel de Espionaje y el del otro, y de cuántas sondas mandas. El código calcula un número:
  - Si tienes más nivel: cantidad de sondas + (diferencia)².
  - Si tienes menos nivel: cantidad de sondas − (diferencia)².
  - Si es igual: tu nivel.
- **Según ese número, el informe muestra:** 1 o menos, solo recursos; 2, también la flota; 3 o 4, también las defensas; 5 o 6, también los edificios; 7 o más, también las investigaciones.
- **Te pueden descubrir:** la probabilidad sube con las naves que tiene el otro y con las sondas que mandas (naves del otro × sondas / 4, con un tope de 100 %). Si te descubren, las sondas se destruyen y dejan escombros de cristal. El otro jugador recibe un aviso de que lo espiaron.

## 12. Misiones de flota

| N.º | Misión | Qué hace |
|---|---|---|
| 1 | Atacar | Pelea contra lo que haya y, si gana, se lleva botín |
| 2 | Ataque en grupo (SAC) | Varias flotas de aliados atacan juntas |
| 3 | Transportar | Lleva recursos a un planeta y vuelve |
| 4 | Desplegar | Deja la flota en otro planeta tuyo |
| 5 | Mantener posición | Deja la flota defendiendo el planeta de un aliado |
| 6 | Espiar | Manda sondas |
| 7 | Colonizar | Funda una colonia en un lugar vacío |
| 8 | Reciclar | Recoge escombros |
| 9 | Destruir | Ataque con Estrellas de la muerte para destruir una luna |
| 15 | Expedición | Viaje a la posición 16 (fuera del sistema) a ver qué se encuentra |

## 13. Expediciones

Al terminar una expedición, el juego tira un número del 0 al 10 (11 resultados, todos igual de probables):

| Resultado | Probabilidad | Qué pasa |
|---|---|---|
| 0, 1, 2 | 27 % | **Pierdes naves:** el 34 %, el 67 % o **el 100 %** de la flota |
| 3 y 7 | 18 % | No pasa nada |
| 4, 5, 6 | 27 % | **Encuentras recursos:** una cantidad al azar cerca de la carga libre (metal la mitad, cristal un cuarto, deuterio un sexto) |
| 8, 9, 10 | 27 % | **Encuentras naves:** se suma una parte de las que llevas, distinta para cada tipo (por ejemplo, 50 % más de colonizadores o de cazadores pesados, 10 % más de naves de carga) |

**Es muy duro:** 1 de cada 11 expediciones pierde la flota entera. Y por un error, la carga libre se calcula con una nave de cada tipo y no con todas (ver §16).

## 14. Protección y juego limpio

| Regla | En Xnova | En OGame |
|---|---|---|
| **Protección de novatos** | Nadie puede atacar, espiar ni mantener posición sobre otro jugador si uno de los dos tiene **más de 5 veces los puntos** del otro; vale en los dos sentidos. Se deja de estar protegido al pasar los 5.000.000 de puntos, un número que en la práctica casi nadie alcanza | Proporción 5 a 1. En universos nuevos: 1 a 5 hasta 50.000 puntos y 1 a 10 hasta 500.000. Si te vuelves inactivo, pierdes la protección |
| **Modo vacaciones** | Mínimo **24 horas** | Mínimo **48 horas** (24 en universos rápidos). No te pueden atacar, pero tampoco produces. No se puede activar con flotas en vuelo o cosas en construcción. Un ataque que ya venía en camino llega igual |
| **Inactivos** | Marca **(i)** a los 7 días sin entrar y **(I)** a los 28 | Igual. La cuenta se borra a los 35 días (salvo que tenga materia oscura comprada sin gastar) |
| **Límite de ataques** | No hay límite automático en el código | Máximo **6 ataques al mismo planeta o luna en 24 horas**. Es una regla que se castiga, no un bloqueo. No cuentan las flotas destruidas por completo ni las sondas. Se suspende en guerras declaradas entre alianzas |
| **Atacar inactivos** | Permitido | Permitido de forma expresa por Gameforge, respetando el límite de ataques y la protección de novatos |

## 15. Puntos y oficiales (lo propio de Xnova)

**Puntos:** se gana **1 punto por cada 1.000 recursos gastados** (el 1.000 se puede cambiar en la configuración). Hay ranking de edificios, de investigaciones, de flota y de defensas, y uno total.

**Experiencia y oficiales:** esto **no existe en OGame**; es invento de Xnova.
- **Experiencia de minero:** cada vez que terminas un nivel de mina o de almacén, ganas 1 punto por cada 1.000 recursos que costó. Si lo demueles, pierdes el triple.
- **Experiencia de saqueador:** **+1 por cada ataque** que haces.
- **Subir de nivel:** el nivel de minero sube cada (nivel × 5.000) de experiencia; el de saqueador, cada (nivel × 10) ataques. Cada nivel nuevo da **1 punto de oficial**. Entre los dos no se pasa de 100 niveles.
- **Con los puntos de oficial** se contratan 15 oficiales, en dos ramas (minera y militar), cada una con un oficial final que abre algo especial:

| ID | Oficial | Qué da | Nivel máx. | Requisitos |
|---|---|---|---|---|
| 601 | Geólogo | +5 % de producción por nivel | 20 | — |
| 602 | Almirante | +5 % de ataque, escudo y casco por nivel | 20 | — |
| 603 | Ingeniero | +5 % de energía por nivel | 10 | Geólogo 5 |
| 604 | Tecnócrata | −5 % del tiempo de construir naves por nivel | 10 | Almirante 5 |
| 605 | Constructor | −10 % del tiempo de construir edificios por nivel | 3 | Geólogo 10, Ingeniero 2 |
| 606 | Científico | −10 % del tiempo de investigar por nivel | 3 | Geólogo 10, Ingeniero 2 |
| 607 | Almacenista | +50 % de almacén por nivel | 2 | Constructor 1 |
| 608 | Defensor | −37,5 % del tiempo de construir defensas por nivel | 2 | Científico 1 |
| 609 | Búnker | Abre el "Protector planetario" | 1 | Geólogo 20, Ingeniero 10, Constructor 3, Científico 3, Almacenista 2, Defensor 2 |
| 610 | Espía | +5 niveles de espionaje | 2 | Almirante 10, Tecnócrata 5 |
| 611 | Comandante | +3 flotas en vuelo a la vez | 2 | Almirante 10, Tecnócrata 5 |
| 612 | Destructor | Construye 2 Estrellas de la muerte por el precio de una | 1 | Espía 1 |
| 613 | General | +25 % de velocidad de las naves | 3 | Comandante 1 |
| 614 | Saqueador | Abre la nave Supernova | 1 | Almirante 20, Tecnócrata 10, Espía 2, Comandante 2, Destructor 1, General 3 |
| 615 | Emperador | Abre el "Destructor planetario" | 1 | Saqueador 1, Búnker 1 |

Los efectos salen de las descripciones del juego. El "Protector planetario" y el "Destructor planetario" no aparecen en los datos de esta versión: parecen ideas que no se terminaron.

**Por qué es interesante:** en Xnova los oficiales **se ganan jugando**, no se compran. Premian por separado al que construye y al que ataca. En OGame (y en 2Moons) los oficiales se pagan con **materia oscura**, que se compra con dinero real.

## 16. Rarezas y errores del código

Conviene saberlos porque, si alguien jugó Xnova, se acostumbró a ellos:

1. **Escombros:** salen del 60 % de las naves destruidas y del 0 % de las defensas, cuando la configuración dice 30 % y 30 %. La cuenta de las naves se hace dos veces.
2. **Defensa y Blindaje cruzados:** Blindaje sube los escudos; Defensa casi no hace nada en la batalla.
3. **Fuego rápido fijo:** no depende de cuántas naves disparan.
4. **Expediciones:** la carga libre se calcula con una sola nave de cada tipo, así que llevar muchas naves de carga no sirve para traer más.
5. **Botín:** si sobra bodega después de cargar, no se vuelve a llenar (OGame sí lo hace).
6. **Supernova:** copia los números del acorazado y figura gastando energía.
7. **Nombres internos cruzados:** en el código, el cañón gauss y el iónico tienen los nombres internos al revés, aunque sus números están bien.
8. **Almacenes:** 100 veces más grandes que en OGame; casi no limitan.
9. **Colonias:** sin límite real (9.000).
10. **Investigación:** unas 5 veces más rápida que en OGame.
11. **Mensajes de espionaje cruzados:** cuando las sondas sobreviven, el informe dice que fueron destruidas, y al revés.

## 17. Lo que agregó 2Moons (la versión más usada después)

| Qué | Detalle |
|---|---|
| Edificio | Universidad (6) |
| Investigaciones | Mejora de procesamiento de metal, cristal y deuterio (131 a 133) |
| Naves | Luna Negra (216), Transportador de Evolución (217), Star Crasher (218), Gigarreciclador (219), Nave de materia oscura (220) |
| Defensas | Protector planetario (409), Cañón de gravitones (410), Estación orbital (411) |
| Oficiales | Los mismos 15 de Xnova, pero **se pagan con materia oscura** (el Geólogo, 1.000 por nivel) |
| Mejoras de 24 horas | Con materia oscura: +10 % de ataque (1.500), +10 % de defensa (1.500), −10 % de tiempo de construcción (750), +10 % de recursos (2.500), +10 % de energía (2.000), −10 % de tiempo de investigación (1.250), −10 % de tiempo de vuelo (3.000) |

## Fuentes

- Código de XNova:Legacies: [xmke/xnova](https://www.github.com/xmke/xnova) (GPL 3)
- Código de 2Moons (tabla `vars` del instalador): [jkroepke/2Moons](https://github.com/jkroepke/2Moons)
- Reglas de OGame (límite de ataques, novatos, inactivos): [Reglas de OGame según Gameforge](https://gameforge.com/en-GB/games/ogame-rules.html), [OGame Wiki: Bashing](https://ogame.fandom.com/wiki/Bashing?oldid=8494), [OGame Wiki: modo vacaciones](https://ogame.fandom.com/wiki/Vacation_Mode), [OGame Wiki: inactivos](https://ogame.fandom.com/wiki/Inactive_Players), [OGame Wiki: protección de novatos](https://ogame.fandom.com/wiki/Newbie_Protection), [foro oficial: protección de novatos](https://board.us.ogame.gameforge.com/index.php?thread%2F103097-newbie-protection-stronger-newbie-mechanics%2F=)
