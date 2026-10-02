# LogsWoW

*Version française : [README.md](README.md) · English version: [README.en.md](README.en.md) · Deutsche Fassung: [README.de.md](README.de.md)*

Lea sus propios registros de combate de World of Warcraft **en su propio
equipo**: sin cuenta, sin subir nada, sin conexión.

El propio juego escribe un archivo, `WoWCombatLog.txt`, que contiene todo
lo que ha ocurrido durante un combate. Los sitios de análisis en línea
leen ese archivo una vez que usted se lo ha enviado. LogsWoW lo lee donde
está.

Si se inicia sin nada más —un doble clic en el archivo, o
`python3 logswow-<version>.pyz`— abre **una ventana**: usted elige un
registro de la lista de los que ha encontrado, marca los combates y el
informe se abre en su navegador. Los mismos pasos existen como comandos,
para quienes prefieren el terminal:

```
python3 -m logswow report "/ruta/a/WoWCombatLog.txt"
```

Junto al archivo aparece una página HTML. Se abre sin conexión, no carga
nada de ninguna parte y no contiene ningún script.

Hay tres presentaciones a elegir, en la ventana o con `--format`:
**onglets** (por defecto: un archivo, la lista de combates a la izquierda
y pestañas por sección), **pages** (una carpeta, una página por combate)
o **longue** (todo en una sola página). Los valores de la opción siguen
en francés, como siempre. En la lista de la izquierda, cada llave está
plegada tras un pequeño «+»: desplegada, muestra sus pulls y sus jefes en
el orden en que se jugaron, y cada pull de trash se abre como un jefe,
con su propio detalle (todo salvo el orden de hechizos, que la llave ya
muestra pull a pull). La página larga no los tiene.

La ventana usa Tkinter, la biblioteca gráfica que viene con Python. En
Windows y con el instalador de macOS de python.org ya está incluida; en
Linux Mint, Ubuntu y Debian se instala una vez con
`sudo apt install python3-tk` (la propia ventana lo indica si falta). Los
comandos no la necesitan.

**Español, inglés, francés o alemán.** La ventana, los comandos y el
informe hablan el idioma de su equipo cuando LogsWoW lo conoce, y si no,
inglés. `--langue es`, `en`, `fr` o `de` impone uno de ellos, y la
variable de entorno `LOGSWOW_LANGUE` fija una elección de una vez por
todas. Los nombres de hechizos, jefes y jugadores se quedan como los
escribió el registro, en el idioma de su cliente de juego.

La traducción al español se ha hecho con cuidado, pero todavía no la han
revisado jugadores nativos. Un término que suene mal puede señalarse: se
corrige en una línea.

## Lo que necesita antes

**Las instrucciones paso a paso para Windows, Linux (incluido Linux
Mint) y macOS están en [`INSTALL.es.md`](INSTALL.es.md).** Cada versión publicada incluye un
único archivo, `logswow-<version>.pyz`, que funciona tal cual:
`python3 logswow-0.10.0.pyz report WoWCombatLog.txt`.

Nada que instalar. Python 3.8 o posterior, y nada más: ningún
`pip install`, ninguna dependencia, ninguna red. El paquete se copia o
se clona, no se instala; a propósito no tiene ni `pyproject.toml` ni
`setup.py`. Las pruebas pasan con Python 3.8 a 3.14; prefiera una versión
que aún reciba mantenimiento (3.10 o posterior en 2026), las antiguas ya
no reciben correcciones de seguridad.

En el juego, dos ajustes, una sola vez:

1. **Registro de combate avanzado** — Sistema → Red → «Registro de
   combate avanzado». Se mantiene de una sesión a otra. Es lo que añade
   al archivo posiciones, salud y recursos.
2. **`/combatlog`** en el chat para empezar a grabar. Esto no se
   conserva: escríbalo de nuevo en cada sesión, o instale un pequeño
   addon que lo haga al entrar en una instancia.

El archivo está en `_retail_\Logs\`. En Linux está dentro de la copia de
la unidad C que mantiene su lanzador (Lutris, Steam con Proton, Bottles,
Wine). Para encontrarlo:

```
python3 -m logswow where
```

## Los comandos

| Comando | Lo que hace |
|---|---|
| *(ninguno)* o `fenetre` | abre la ventana |
| `report ARCHIVO` | escribe la página HTML completa |
| | `--format onglets\|pages\|longue` la presentación, `-o` el nombre del archivo (la carpeta para `pages`), `--only` un solo combate, `--pull-gap` cómo se separan los pulls, `--wowhead` el idioma de los enlaces, `--sans-sequence` sin el orden de hechizos, `--force` para sobrescribir un archivo que no es un informe |
| `list ARCHIVO` | lista los combates del archivo, uno por línea |
| `diagnose ARCHIVO` | muestra lo que el lector ha entendido, y lo que no |
| `where` | busca la carpeta `Logs` del juego |
| *(todos)* | `--langue es\|en\|fr\|de\|auto` el idioma de la interfaz y del informe |

**Ejecute `diagnose` primero**, tras cada parche del juego. Muestra la
disposición de los campos tal como se ha *medido en su archivo*, la lista
de eventos encontrados y cada línea que no ha podido ubicar. Un informe
de combate seguro de sí mismo, sacado de un archivo mal leído, sería peor
que ningún informe.

## Lo que contiene el informe

- **Los combates**: cada pull de jefe y cada llave de Mítica+, con su
  duración, su resultado y su número de muertes. Una llave y los jefes
  que contiene aparecen ambos. Un encuentro que el juego abre y cierra
  sin que llegue un solo golpe se llama «sin combate» y no cuenta como
  derrota.
- **La composición del grupo**, tanques, sanadores y DPS, con la clase y
  la especialización de cada uno. Proceden de lo que el cliente escribe
  al comienzo del combate; una especialización que la herramienta no
  conoce se muestra con su número en lugar de adivinarse.
- **Una línea de tiempo** del daño recibido por el grupo, segundo a
  segundo, con una escala rotulada a la izquierda y las muertes en rojo.
  Como curva, en un pull de jefe, la salud del jefe (nombrado bajo el
  gráfico); en una llave, **la salud conjunta de todo lo atacado**, la
  suma de la salud actual entre la suma de los máximos, que sube con cada
  pack y baja cuando muere.
- **La lista de pulls** en cuanto un combate contiene varios, como toda
  llave de Mítica+: inicio, duración, lo que se atacó y cuántos, daño
  infligido, daño recibido, muertes. Un pull que contiene un jefe lo
  nombra primero, lleva una insignia con el resultado del encuentro
  (victoria en verde, derrota en rojo) y separa **el daño al jefe del daño
  al trash** arrastrado con él. Los límites de un encuentro vienen del
  propio registro: un encuentro al que ninguna unidad da nombre (un
  consejo, un dúo) cuenta sobre el jefe todo el daño infligido mientras
  dura, y la página lo dice. Un pull termina tras tres segundos sin daño
  en ningún sentido, salvo dentro de un encuentro con un jefe, que
  siempre es un solo pull; `--pull-gap` cambia ese umbral si su grupo
  encadena packs.
- **Quién abrió cada pull**, bajo su fila: el primer acto que vincula al
  grupo con un enemigo desde el final del pull anterior, con el jugador,
  su rol, el hechizo (el de una invocación cuenta para su amo) y la
  antelación sobre el primer golpe. El registro no tiene ninguna línea
  de amenaza: un enemigo atraído por proximidad solo se ve por lo que
  hace después, y la línea, marcada como **beta**, dice entonces «Golem
  actuó primero, sobre Tisane». Como una sanación, un beneficio o una
  disipación dados en combate atraen al enemigo hacia quien los dio,
  también indica cuándo ese objetivo acababa de dar uno, y a quién: ese
  suele ser el verdadero responsable. Hechos, no veredictos.
- **El primer golpe que recibió cada enemigo** en cada pull, jefes
  incluidos, desplegable bajo su fila: quién lo tocó primero (un golpe
  fallado cuenta), con qué hechizo, en qué momento. Ese es seguro: el
  registro lo escribe tal cual.
- **Daño y sanación** por jugador, con DPS, HPS y la parte de la sanación
  perdida en sobresanación. **Los escudos** tienen su propia columna: lo
  que absorbieron no es una sanación en el registro, ya que evitan daño en
  lugar de devolver salud. La columna «Suma» añade ambos; ese total es lo
  que los sitios en línea llaman «sanación». El daño cuenta lo que cada
  golpe quitó de verdad: no el exceso de un golpe mortal, pero sí lo que
  se tragó el escudo de un enemigo. La sanación cuenta lo que se tragó un
  perjuicio de absorción de sanación, y Enlace de espíritu, que mueve
  salud de un jugador a otro, no es ni sanación ni daño recibido.
- **Comparado con Warcraft Logs** en cinco llaves, jugador por jugador:
  las mismas muertes para todos, el mismo daño con una diferencia de
  0,1 % como mucho (exacto a la unidad para la mitad de los jugadores),
  la misma sanación exacta a la unidad para 17 jugadores de 25. Las
  diferencias restantes tienen una causa conocida, descrita en
  `CHANGELOG.md`.
- **Los hechizos lanzados** incluyen los de las invocaciones, mostrados
  aparte. El archivo escribe un hechizo que el juego activa solo igual que
  uno pulsado a mano, así que la cifra es más alta que la de un sitio en
  línea, que elimina los procs con una lista mantenida.
- **El daño que el archivo no atribuye a nadie**, si lo hay: una criatura
  aliada cuyo amo el registro nunca nombra no puede vincularse a ningún
  jugador. Queda fuera del total, y un recuadro lo dice, con nombres y
  cantidades; un total silenciosamente incompleto sería peor.
- **La parte de un Evocador Aumento**: el registro atribuye a sus
  beneficios (Poder de ébano, Presciencia…) una parte de los golpes de
  otros jugadores, y a él los Bombardeos que activa un aliado. Esas
  cantidades ya están en el daño de quienes dieron los golpes: se
  muestran aparte en el panel del Evocador, nunca se suman una segunda
  vez. Warcraft Logs, en cambio, las traslada al Evocador: la columna
  **Reatribuido** de la clasificación de daño hace ese mismo traslado,
  junto al total y no en su lugar, en cuanto un combate contiene esas
  líneas.
- **Las llaves abandonadas**: una llave reiniciada o dejada por otra está
  «abandonada», no «fuera de tiempo», y el recuadro **Llaves sin
  terminar** cuenta también la que el registro deja abierta.
- **A tiempo o fuera de tiempo**: el registro dice que una llave se
  completó, nunca si fue a tiempo, y no escribe el cronómetro de la
  mazmorra. El veredicto viene de la puntuación que el juego escribe al
  final de la llave: una llave a tiempo da al menos la puntuación base de
  su nivel, la de la tabla que publica Raider.IO (125 + 15 × nivel, más
  15 en cada escalón de afijos: +4, +7, +10 y +12; 320 para un +10, 380
  para un +13), una tardía menos. Medido en 14 llaves completadas: las 13
  a tiempo de 3 a 15 puntos por encima, la única tardía 60 puntos por
  debajo, y los temporizadores de la temporada que da Raider.IO confirman
  cada uno de estos veredictos. Sin puntuación (formato antiguo), la
  llave solo está «completada».
- **Vista previa y comparación de llaves en la ventana.** Bajo la lista de
  combates, tres pestañas siguen lo que marque: resumen, llaves, equipo.
  Dos llaves terminadas de la misma mazmorra y del mismo nivel se
  comparan: daño/s, sanación/s (escudos incluidos) y, para el tanque,
  daño recibido/s, para el grupo y para cada jugador. La página lleva la
  misma comparación.
- **El equipo de los jugadores**, en el resumen de cada combate: nivel de
  objeto medio del grupo y, plegada, cada pieza con su nivel, sus
  encantamientos y sus gemas. El registro solo da el número y el nivel de
  un objeto: el nombre y el icono vienen de la base de objetos del juego,
  que LogsWoW no tiene; cada objeto es un número con un enlace a Wowhead,
  que solo se sigue si hace clic.
- **Golpes cuerpo a cuerpo recibidos**, en el panel de cada jugador al
  que el enemigo golpeó al menos diez veces (sobre todo el tanque):
  impactos, críticos, absorbidos por completo, parados, esquivados,
  fallados, bloqueados, tal como los escribe el registro. Y la parte de
  los impactos que **llegaron por la espalda**: el registro no lo
  escribe, LogsWoW lo deduce de la posición del atacante y de la
  orientación del jugador. Es una estimación fiable, no un dato escrito,
  y limitada al cuerpo a cuerpo; la página lo dice, con un control: el
  juego no permite parar ni esquivar por la espalda, y del 97 al 98 %
  de las paradas y esquivas cae delante en las llaves medidas.
- **Físico o mágico**: la parte del daño recibido e infligido que fue
  física, mágica o ambas, en porcentaje, en todo el combate y luego pull a
  pull, con el detalle por escuela (Sombras, Fuego, Naturaleza…).
- **Lo que ha hecho daño al grupo**: cada habilidad enemiga, cuánto costó
  y a cuántos jugadores alcanzó.
- **Las muertes**, cada una con la cadena de los últimos golpes y
  sanaciones recibidos antes del final, y la salud restante en cada paso.
- **Lo que el grupo impidió**: cuántos hechizos empezó el enemigo, cuántos
  se completaron, cuántos cortó una interrupción y cuántos terminaron
  porque murió el lanzador.
- **Por jugador**, desplegando su nombre: para cada hechizo, el total, la
  parte, el número de lanzamientos y de golpes, la media, el porcentaje
  de críticos, el valor por segundo y el objetivo principal. Después su
  sanación con la sobresanación y a quién fue, lo que recibió y de quién,
  los beneficios recibidos **con quién los dio**, los perjuicios
  sufridos, lo que aplicó él mismo y a quién, sus interrupciones y
  disipaciones con el nombre de lo cortado, y sus pausas más largas sin
  lanzar nada.
- **El orden de hechizos, pull a pull**, al final del panel de cada
  jugador: cada hechizo lanzado, en orden, como una ficha de color fijo
  con sus dos primeras letras. Al pasar el ratón aparecen su nombre y el
  momento del lanzamiento, un clic abre Wowhead. La leyenda es un filtro:
  un clic en un hechizo oculta o muestra todas sus fichas, sin ningún
  script en la página. Los hechizos de sus invocaciones van aparte, como
  fichas redondas. Los que el juego activa solo están escritos en el
  registro igual que una pulsación; los que tienen sus rasgos (nunca
  pagados, y lanzados a la vez que un hechizo pagado, o más rápido que
  cualquier botón, o la segunda copia de un hechizo que el registro
  escribe dos veces con el mismo nombre) se agrupan aparte y empiezan
  ocultos; un clic los muestra. `--sans-sequence` omite la sección, para
  una página de la mitad de tamaño aproximadamente.
- **Por enemigo**, del mismo modo: las unidades con el mismo nombre se
  agrupan, con lo que infligieron y a quién, lo que recibieron y de quién,
  los hechizos que lanzaron y cuántas murieron.
- **El JcJ, en parte**: en una arena o un campo de batalla, los
  jugadores del otro bando (fuera del grupo y hostiles, tal como el
  registro los escribe) son enemigos, nunca el grupo; un miembro del grupo
  bajo un control mental sigue en el grupo. Las partidas aún no se
  separan: sin encuentro ni llave en el archivo, todo el registro forma
  una sola «sesión».
- **Los nombres de hechizos son enlaces a Wowhead**, en el idioma de su
  equipo. `--wowhead es` impone un idioma, `--wowhead off` quita los
  enlaces. No se carga nada al abrir la página: un enlace solo se sigue si
  usted hace clic en él.

Una tarde entera produce una página de varios megabytes. Para ver solo
una parte:

```
python3 -m logswow list WoWCombatLog.txt          # ver los combates
python3 -m logswow report WoWCombatLog.txt --only 5
python3 -m logswow report WoWCombatLog.txt --only "Nalorakk"
```

## Lo que no hace, y por qué

- **No le compara con nadie.** Un percentil necesita los registros de
  todos los demás jugadores. Es justo lo que no tiene una herramienta
  local en su equipo, y es el único servicio real que presta un sitio
  centralizado.
- **No dice si un golpe era evitable.** El archivo dice quién recibió el
  golpe y cuánto; saber que un daño venía de un efecto en el suelo
  requiere conocer al jefe. Esta herramienta no pretende saberlo.
- **No sabe qué es un control.** El registro nunca escribe que un hechizo
  sea un aturdimiento o un miedo. Un hechizo enemigo que se detiene sin
  interrupción y sin que muera el lanzador se clasifica por tanto como
  «causa no indicada por el registro». Distinguir un control de un simple
  perjuicio requeriría una lista de hechizos mantenida.
- **No calcula un porcentaje de mitigación.** El registro nunca escribe
  lo que un golpe habría hecho *antes* de la armadura y las reducciones de
  daño. El segundo número de cada golpe lo parece y no lo es: medido en
  una llave real, vale 1,03 veces el daño recibido en un golpe normal y
  2,59 veces en un crítico; es la cantidad antes del multiplicador de
  crítico. Dividir uno por otro da un porcentaje creíble y falso. Lo que
  sí está en el archivo, y se muestra, es el **daño absorbido** por los
  escudos.
- **No calcula un aDPS al estilo de FF Logs.** FF Logs no lee en el
  registro la parte de un beneficio: la calcula, a partir de una tabla
  mantenida del multiplicador de cada beneficio y, para un beneficio de
  golpe crítico, de la probabilidad de que el crítico viniera de él. El
  registro de WoW solo escribe él mismo esa parte para los beneficios de
  un Evocador, y es exactamente lo que muestra la columna
  **Reatribuido**: la fórmula del rDPS (daño − parte debida a los
  beneficios de otros + parte dada a otros), limitada a esos beneficios.
  Para los demás haría falta la misma tabla mantenida; y un beneficio de
  celeridad (Ansia de sangre, Infusión de poder) cambia el número de
  golpes, algo que ninguna de esas fórmulas trata.
- **No juzga su rotación.** Muestra sus pausas, sus habilidades y sus
  efectos activos. Decir «aquí debería haber pulsado esto» requiere las
  reglas de su especialización, escritas y mantenidas por alguien que la
  juegue.

Estos límites son estructurales, no funciones que falten.

## Dónde están sus datos

En su disco, y en ningún otro sitio. El programa abre un archivo,
escribe un archivo y termina. No abre ninguna conexión de red, no lee
ninguna configuración, no escribe ninguna caché y no conoce ninguna
cuenta. La página que produce no carga nada al abrirse: la prueba
`test_writes_a_self_contained_page` falla si se cuela un `<script>`, una
hoja de estilos, un `src=`, un `@import` o un `url(`, y si aparece una
dirección distinta de Wowhead. Los enlaces a Wowhead solo se siguen si
usted hace clic en ellos.

El informe nunca escribe el **reino** de un jugador: los nombres aparecen
en su forma corta, en las tablas como en las cadenas de muerte. Una
captura del informe identifica por tanto menos que una captura del
registro.

Un recordatorio útil: un registro de combate contiene los nombres y el
rendimiento de **todo el grupo**, no solo los suyos. **El informe HTML
también**: sin los reinos, pero con el nombre corto, el daño, la sanación
y las muertes de cada uno. Compártalo solo con el acuerdo de quienes
aparecen en él, como haría con el propio registro.

`report` se niega a escribir encima de un archivo existente que no sea un
informe de LogsWoW (otro registro, por ejemplo), salvo con `--force`, y
nunca escribe encima del registro que lee, ni siquiera con `--force`.

## Pruebas, y verificación con un registro real

```
python3 tests/run-tests.py
python3 tools/check-invariants.py WoWCombatLog.txt
ln -s ../../tools/pre-push .git/hooks/pre-push     # una vez, para quien contribuya
```

Las pruebas se ejecutan sin dependencias y sin red sobre
`examples/exemple-combat.txt`, un registro **inventado** para este
repositorio: ningún registro real se incluye nunca, precisamente por el
recordatorio anterior. Las pruebas leen francés sea cual sea el idioma
del equipo; las de los demás idiomas piden el suyo.

El segundo script toma un registro **real** y comprueba que las cuentas
cuadran: el daño del grupo es la suma del de los jugadores, el de un
jugador la suma de sus hechizos, el de un hechizo la suma sobre sus
objetivos; lo mismo para la sanación; las muertes contadas de tres
maneras dan el mismo número; ninguna duración de efecto supera la del
combate; los hechizos enemigos iniciados son iguales a la suma de sus
resultados; la parte que el juego acredita a un Evocador es igual a la
que se descuenta a los jugadores. Encontró un error la primera vez que
se ejecutó. No dice si un número es verdadero, solo si los números
concuerdan entre sí. Revisa todo el archivo incluso tras un primer fallo,
y hace el balance al final.

Nada se ejecuta en línea al hacer un push: el hook `tools/pre-push`
repite estas comprobaciones en su equipo antes de cada push. Solo
**publicar una versión** pasa por una acción de GitHub
(`.github/workflows/release.yml`), iniciada o bien con el botón «Run
workflow» de la pestaña Actions (en `main`), o bien con una etiqueta como
`v0.2.0` enviada desde una copia del repositorio: vuelve a ejecutar las
pruebas, comprueba que la etiqueta es la versión del paquete y está en
`main`, construye el `.pyz` y su huella `SHA256SUMS`, y los publica con
las notas de la versión. Solo usa lo que ya tiene la máquina de GitHub,
sin ninguna acción de terceros.

Lo que cambia de una versión a otra está en
[`CHANGELOG.es.md`](CHANGELOG.es.md) (desde 0.10.0; las versiones
anteriores en francés en [`CHANGELOG.md`](CHANGELOG.md), y desde 0.9.0
en inglés en [`CHANGELOG.en.md`](CHANGELOG.en.md)); el detalle técnico,
fechado y medido, en las secciones fechadas de `CLAUDE.md`.

El registro se lee tal como lo escribe el juego, con sus finales de línea
de Windows, en Linux igual que en Windows.

## Licencia

GNU Affero General Public License, **versión 3 o (a su elección)
cualquier versión posterior** (AGPL-3.0-or-later), desde la versión
0.8.0. Cualquiera puede usarlo, modificarlo y redistribuirlo; quien
distribuya una versión, modificada o no, debe proporcionar su código
fuente bajo la misma licencia. La AGPL añade un punto a la GPL: **quien
ofrezca una versión modificada como servicio en línea** (un sitio que
leyera sus registros, por ejemplo) debe ofrecer también su código fuente
a quienes lo usen. Para usted, que lo usa en su equipo, no cambia nada.
Desde el 28 de septiembre de 2026, las versiones anteriores (0.1.0 a
0.7.0) también se distribuyen bajo AGPL-3.0-or-later; quien ya tuviera
una copia conserva, para esa copia, los derechos de la GPL con la que la
recibió, que la GPL declara irrevocables. Véanse `LICENSE` y
`PROVENANCE.md`.

El texto que hace fe es el de la licencia en inglés, en `LICENSE`; este
resumen es solo orientativo.
