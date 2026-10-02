# Historial de versiones

Lo que cambió cada versión publicada, para quienes la usan. Este
historial en español empieza con la 0.10.0, la primera versión que habla
español; las versiones anteriores se describen en francés en
[`CHANGELOG.md`](CHANGELOG.md) (desde la 0.9.0 también en inglés en
[`CHANGELOG.en.md`](CHANGELOG.en.md)), y el detalle técnico, fechado y
medido, está en las secciones fechadas de `CLAUDE.md`.

## 0.15.0 — 2026-10-02

**Una vista previa en la ventana, antes de escribir la página.** Bajo la
lista de combates, tres pestañas siguen lo que marque: *Resumen*
(duración, daño, sanación, muertes y una línea por jugador), *Llaves* (la
comparación, más abajo) y *Equipo*. Ve lo que diría el informe y solo
escribe la página si quiere ir más lejos.

**Comparar dos llaves de la misma mazmorra y del mismo nivel**, en la
ventana y en la página («Comparación de llaves», bajo la lista de
combates), con, para el grupo y para cada jugador: el **daño por
segundo**, la **sanación por segundo** (escudos incluidos, como los
sitios en línea), las muertes, y para el **tanque** el **daño recibido
por segundo** (lo que absorbieron los escudos cuenta). La diferencia es la
de la última llave respecto a la primera. Solo se comparan llaves
terminadas; una llave abandonada o de otro nivel queda aparte.

**El equipo de los jugadores, en el resumen de cada combate.** El nivel de
objeto medio del grupo y, plegado bajo la composición, el equipo de cada
uno: ranura, nivel, encantamientos, gemas. El registro da el número y el
nivel de cada objeto, nunca su nombre, su icono ni sus estadísticas: vienen
de la base de objetos del juego, que LogsWoW no tiene (no se conecta a
nada). Cada objeto es, por tanto, un número con un enlace a Wowhead, que
solo se sigue si hace clic. El nivel medio sigue la fórmula del juego
(dieciséis ranuras, sin camisa ni tabardo, un arma a dos manos contada dos
veces). Leído en 420 líneas de cinco registros: dieciocho ranuras cada vez.
Ninguna otra cifra cambia.

## 0.14.0 — 2026-09-29

**Golpes cuerpo a cuerpo recibidos, sobre todo para el tanque.** El
panel de cada jugador al que el enemigo golpeó al menos diez veces tiene
una sección nueva: cuántos golpes impactaron (de ellos críticos), cuántos
fueron absorbidos por completo, parados, esquivados, fallados o
bloqueados, y la parte evitada. Todo eso lo escribe el registro.

También da la parte de los impactos que **llegaron por la espalda**. Ahí
el registro no dice nada: LogsWoW lo deduce de la posición del atacante
y de la orientación del jugador, que el registro da línea a línea. Es
una estimación fiable, no un dato escrito, y limitada al cuerpo a
cuerpo; la página lo dice, con un control sobre el propio combate: el
juego no permite parar ni esquivar un golpe por la espalda, y en las
cuatro llaves del propietario del 29 de septiembre, del 97 al 98 % de
las paradas y esquivas del tanque cae delante. El mismo tanque recibió
del 24 al 34 % de sus impactos por la espalda, según la llave. Ninguna
otra cifra cambia.

## 0.13.1 — 2026-09-29

**La barra de progreso de la ventana se ve, y dice el tiempo que
queda.** Sí avanzaba, pero en Linux el tema de la ventana la dibujaba
gris claro sobre fondo gris, y se vaciaba en cuanto terminaba la
lectura: parecía rota. Ahora es azul, se queda llena cuando la lectura o
el informe han terminado, y sigue la posición real en el archivo en
lugar de una estimación por línea. Debajo, la línea de estado da el
porcentaje y el tiempo restante: «Leyendo… 36 %, 401.409 líneas leídas,
quedan unos 30 s». En el registro de 364 MB del propietario, la
estimación anunciaba 45 s a los cuatro segundos, para 46 s reales, y
nunca se alejó más de 3 s. El informe se escribe en uno o dos segundos:
no tiene cuenta atrás.

## 0.13.0 — 2026-09-29

La auditoría completa de la 0.12.1, comprobada en su registro de 364 MB
del 29 de septiembre.

**Corrección: las pausas de un jugador con mascota quedaban ocultas.**
Cada hechizo lanzado por una mascota, una invocación o un tótem ponía fin
a la pausa de su dueño: un cazador que no lanzó nada durante cuarenta
segundos, mientras su mascota mordía cada segundo, mostraba cero segundos
sin acción. Ahora solo cuentan los hechizos del propio jugador para el
«Tiempo sin acción» y las pausas más largas; los de sus invocaciones
siguen contados, aparte, entre los hechizos lanzados. En su registro
cambian 14 jugadores de 25; el más afectado pasa de 283 s a 458 s sin
acción en una llave.

**Corrección: en JcJ, el adversario se contaba en el grupo.** En una
arena o un campo de batalla, el registro escribe a los jugadores del
otro bando fuera del grupo y hostiles; se trataban como compañeros: el
adversario figuraba en la clasificación, cada golpe intercambiado
contaba como recibido de un aliado, y el daño infligido se quedaba en
cero. Ahora son enemigos, con sus mascotas, sus lanzamientos (que una
interrupción puede cortar) y sus muertes. Un miembro del grupo bajo un
control mental, o que sale del grupo un momento, sigue en el grupo. Las
partidas aún no se separan. En su registro de mazmorra no cambia ninguna
cifra.

**Algunas palabras seguían en francés en los informes en inglés, alemán
y español**: «et 3 autre(s)» en la tabla de pulls, «autres» en el
reparto por escuela y entre los objetivos de un sanador, «aucun» y
«absent» al pie de la página y en `diagnose`, «Mo» en `where`. Todo está
traducido.

**Un tamaño de archivo se escribe igual en todas partes.** La ventana
contaba un megabyte como un millón de bytes; la página, `diagnose` y
`where` como 1.048.576: el mismo registro medía allí 364,4 MB y aquí
347,5 MB. Ahora es un millón de bytes en todas partes, como dice el
nombre de la unidad y como lo muestra un gestor de archivos en Linux.
`diagnose` escribe también sus números al estilo de su idioma
(«1.121.188 líneas»).

**Menos memoria para escribir el informe.** La página se montaba entera
en memoria, varias veces, antes de escribirse; ahora va al disco combate
a combate. En su registro: 252 MB → 89 MB en el pico para la vista con
pestañas, 149 MB → 88 MB para la página larga. La página escrita es
idéntica byte a byte.

Más pequeño: `-q` tiene su línea de ayuda; «1 descartado, demasiado
pequeño» concuerda en singular; las pruebas pasan también con Python 3.14.

## 0.12.1 — 2026-09-29

**Corrección: el umbral «a tiempo» era demasiado exigente de +2 a +11.**
La regla de la 0.12.0, 15 × nivel + 185, acertaba desde +12 pero pedía
por debajo de 15 a 30 puntos de más: un +10 a tiempo con 330 puntos
habría aparecido «fuera de tiempo». El umbral es ahora la puntuación base
que Raider.IO publica para cada nivel de +2 a +30: 125 + 15 × nivel, más
15 en cada escalón de afijos (+4, +7, +10 y +12), es decir 320 para un
+10 y 335 para un +11 (de +12 en adelante nada cambia). Ninguna llave de
los registros del propietario cambia de veredicto, pero un Murder Row
+10 en 19:16, con 335 puntos justos, solo pasaba por empate. Los
temporizadores de la temporada, tal como los da la API de Raider.IO,
confirman los 14 veredictos de esos registros.

## 0.12.0 — 2026-09-29

**Corrección: «a tiempo» era falso para una llave terminada tarde.** Un
Val Aveuglant +13 completado en 30:23 aparecía «a tiempo». El registro
escribe, al final de una llave, un indicador que significa «completada»,
no «cronometrada», y nunca escribe el tiempo límite de la mazmorra. Lo
que las distingue es la puntuación que el juego da a la llave: al menos
15 × nivel + 185 a tiempo (380 para un +13), menos si llega tarde. Los
dos Val Aveuglant +13 del propietario: 383,2 en 27:26 (a tiempo), 319,5 en
30:23 (fuera de tiempo). De 15 llaves completadas, las 14 a tiempo están
todas por encima del umbral; si un veredicto parece falso, diga qué
llave. Una llave de un registro antiguo, sin puntuación, solo está
«completada».

**Los pulls en la lista de la izquierda.** Cada llave está ahora plegada
tras un pequeño «+». Desplegada, muestra sus pulls y sus jefes en el
orden en que se jugaron («Pull 1», «Pull 2», el jefe, «Pull 4»…), con la
misma numeración que la tabla de pulls. Cada pull de trash se abre como
un jefe, con su propio detalle: daño, sanación, muertes, jugadores,
enemigos (el orden de hechizos sigue en la vista de la llave, pull a
pull). Hacer clic en el nombre de la llave la selecciona, el «+» la
despliega. La carpeta de páginas tiene también una página por pull; la
página larga no cambia.

Estas vistas tienen un coste, medido en un registro de 364 MB: 35 s → 45
s, 13 → 20 MB de página, 163 → 249 MB de memoria máxima. Todas las cifras
de los combates son idénticas a la 0.11.0, y cada pull cuenta
exactamente el mismo daño que su fila en la tabla de la llave (comprobado
en 143 pulls de cinco registros).

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
