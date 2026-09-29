# Historial de versiones

Lo que cambió cada versión publicada, para quienes la usan. Este
historial en español empieza con la 0.10.0, la primera versión que habla
español; las versiones anteriores se describen en francés en
[`CHANGELOG.md`](CHANGELOG.md) (desde la 0.9.0 también en inglés en
[`CHANGELOG.en.md`](CHANGELOG.en.md)), y el detalle técnico, fechado y
medido, está en las secciones fechadas de `CLAUDE.md`.

## 0.11.0 — 2026-09-29

**El primer golpe que recibió cada enemigo**, pull a pull, jefes
incluidos: para cada monstruo, el jugador que lo tocó primero (un golpe
fallado también cuenta, atrae al monstruo igual), con qué hechizo y en
qué momento del pull. El hechizo de una mascota, una invocación o un
tótem cuenta para su amo. El registro lo escribe tal cual: es seguro. La
lista se despliega bajo cada fila de la tabla de pulls, y bajo el
encabezado de un combate de jefe solo.

**Quién abrió cada pull.** Bajo cada fila de la tabla de pulls, el primer
acto que vincula al grupo con un enemigo desde el final del pull
anterior: «Abierto por Tisane (tanque): Atracción letal, 0,4 s antes del
primer golpe». El hechizo de una mascota, una invocación o un tótem
cuenta para su amo, y el rol del jugador aparece junto a su nombre. El
registro no tiene ninguna línea de amenaza: un enemigo atraído por
proximidad (un body pull) solo se ve por lo que hace después, y la línea
dice entonces «Golem actuó primero, sobre Braise», marcada como **beta**
a la espera de comentarios. Como una sanación, un beneficio o una
disipación dados en combate atraen al enemigo hacia quien los dio,
añade, cuando es el caso, que ese objetivo acababa de ayudar a otro
jugador, y a cuál: a menudo es él quien tiró. Hechos, no veredictos: un
efecto en el suelo dejado por el pack anterior también puede hacer que
un enemigo actúe primero.

Medido en tres registros reales de mazmorra (159 pulls): el tanque abre
la mayoría de los pulls, normalmente entre 0,3 y 0,6 s antes del primer
golpe; el enemigo actúa primero en aproximadamente un pull de cada seis.

**Un pull termina tras 3 segundos sin daño**, en lugar de 6: más cerca de
lo que hace un grupo en el juego. `--pull-gap` y el ajuste de la ventana
siguen permitiendo elegir otro valor. Los totales no cambian; solo la
división en pulls es más fina.

## 0.10.0 — 2026-09-28

**LogsWoW también habla alemán y español.** La ventana, los comandos,
`diagnose` y el informe existen ahora en cuatro idiomas. La elección
sigue siendo automática (el idioma de su equipo, inglés para un idioma
sin traducción); `--langue de` o `--langue es` impone uno. Cada idioma
escribe sus números a su manera: «25,4 Mio.» y «25.361.906» en alemán,
«25,4 M» y «45,6 mil» en español. Las traducciones se han escrito con
cuidado, pero todavía no las han revisado jugadores nativos: un término
que suene mal puede señalarse, se corrige en una línea.

**La coma decimal en francés.** «25,4 M» y «180,6 Mo» en lugar de
«25.4 M» y «180.6 Mo», en todas partes.

**Las llaves abandonadas se reconocen.** Una llave reiniciada, o dejada
por otra, se contaba «fuera de tiempo»; ahora está «abandonada». El
juego escribe, antes de cada llave nueva, un final vacío (ni nivel ni
tiempo) que cierra la que seguía abierta. Un recuadro nuevo en la parte
superior del informe, **Llaves sin terminar**, cuenta esas llaves y la
que el registro deja abierta («interrumpido»).

**La columna «Reatribuido»**, en la clasificación de daño, en cuanto un
combate contiene las líneas de apoyo de un Evocador: el daño de cada
jugador, menos la parte que el juego acredita a los beneficios de un
Evocador (Poder de ébano, Presciencia, Bombardeos…), más lo que le
acredita a él. Es la reatribución de Warcraft Logs, y la única forma de
«aDPS» que permite el registro: nunca escribe lo que un Ansia de sangre
o una Infusión de poder añadió a los golpes de los demás. La columna va
junto al total y no en su lugar, y el total del grupo no cambia.

**Corrección.** En inglés, el tamaño del archivo aparecía en «Mo»; es
«MB».

Nada más cambia: en cinco registros (tres de ellos reales), ningún
número se mueve salvo las dos llaves abandonadas, y los cuatro idiomas
dan exactamente los mismos números. La velocidad es la misma.
