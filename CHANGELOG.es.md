# Historial de versiones

Lo que cambió cada versión publicada, para quienes la usan. Este
historial en español empieza con la 0.10.0, la primera versión que habla
español; las versiones anteriores se describen en francés en
[`CHANGELOG.md`](CHANGELOG.md) (desde la 0.9.0 también en inglés en
[`CHANGELOG.en.md`](CHANGELOG.en.md)), y el detalle técnico, fechado y
medido, está en las secciones fechadas de `CLAUDE.md`.

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
