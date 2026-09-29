# Instalar y ejecutar LogsWoW

*Version française : [INSTALL.md](INSTALL.md) · English version: [INSTALL.en.md](INSTALL.en.md) · Deutsche Fassung: [INSTALL.de.md](INSTALL.de.md)*

LogsWoW solo necesita **Python 3.8 o posterior**. No hay nada más que
instalar: ninguna biblioteca, ninguna cuenta, ninguna conexión. Hay dos
maneras de obtenerlo, y la primera casi siempre basta:

- **El archivo único `logswow-0.10.0.pyz`**, adjunto a cada versión
  publicada (página «Releases» del repositorio). Es todo el programa en
  un solo archivo de unos 170 KB, que funciona tal cual desde cualquier
  carpeta.
- **El código fuente** (botón «Code» y luego «Download ZIP», o
  `git clone`), para quien quiera leer el código o ejecutar las pruebas.

El repositorio es público: no hace falta ninguna cuenta para descargar.
También puede simplemente pasar el archivo `.pyz` a otra persona: no se
necesita nada más.

En los ejemplos de abajo, sustituya `0.10.0` por el número de la versión
que haya descargado.

LogsWoW habla el idioma de su equipo cuando lo conoce (español, inglés,
francés, alemán), y si no, inglés. Añada `--langue es` a un comando para
imponer el español, o fíjelo de una vez por todas con la variable de
entorno `LOGSWOW_LANGUE=es`.

---

## Primero, en el juego (una vez)

1. **Registro de combate avanzado**: Sistema → Red → marque «Registro de
   combate avanzado». El ajuste se mantiene de una sesión a otra. Sin él,
   el archivo no contiene ni la salud ni las posiciones, y varias curvas
   del informe quedan vacías.
2. **`/combatlog`** en la ventana de chat, al comienzo de cada sesión de
   juego, para empezar a grabar. Esto no se conserva: escríbalo de nuevo
   en cada conexión (o use un pequeño addon que lo haga al entrar en una
   instancia).

El juego escribe entonces `WoWCombatLog-<fecha>.txt` en su carpeta
`Logs`.

---

## Windows 10 y 11

### 1. Instalar Python

1. Descargue el instalador para Windows desde **python.org**
   («Downloads», versión 3.12 o posterior).
2. En la primera pantalla del instalador, **marque «Add python.exe to
   PATH»** y luego «Install Now».
3. Compruébelo: abra el Símbolo del sistema (tecla Windows, escriba
   `cmd`, Intro) y escriba:

   ```
   py --version
   ```

   Debería aparecer una línea `Python 3.x.y`.

> Si al escribir `python` se abre Microsoft Store en lugar de responder,
> es un atajo de Windows, no Python: use `py`, que instala python.org, o
> desactive el atajo en Configuración → Aplicaciones → Configuración
> avanzada de aplicaciones → Alias de ejecución de aplicaciones.

### 2. Obtener LogsWoW

Descargue `logswow-0.10.0.pyz` y guárdelo donde quiera, por ejemplo en
`Documentos\LogsWoW`.

### 3. Ejecutarlo

**Haga doble clic en `logswow-0.10.0.pyz`**: se abre la ventana de
LogsWoW. Lista los registros que ha encontrado (en las unidades C: a
H:), usted elige uno, luego los combates, y «Crear el informe y abrirlo»
muestra la página en su navegador.

Detrás se abre también una ventana negra: es normal. Para dejar de
verla, cambie el nombre del archivo a `logswow-0.10.0.pyzw` (con una
**w** al final); para tenerlo en el escritorio: clic derecho → Enviar a
→ Escritorio (crear acceso directo).

Si el doble clic no inicia nada, o para usar los comandos: en el Símbolo
del sistema, vaya a esa carpeta y luego:

```
cd %USERPROFILE%\Documents\LogsWoW
py logswow-0.10.0.pyz where
```

`where` muestra la carpeta `Logs` del juego (busca en las unidades C: a
H:) y los últimos registros que contiene. Después:

```
py logswow-0.10.0.pyz report "C:\Program Files (x86)\World of Warcraft\_retail_\Logs\WoWCombatLog-091826_203000.txt"
```

La página HTML (organizada en pestañas; `--format pages` o
`--format longue` para las otras presentaciones) aparece junto al
registro, con el mismo nombre terminado en `.html`; un doble clic la abre
en su navegador. Para escribirla en otro sitio, añada por ejemplo
`-o %USERPROFILE%\Documents\LogsWoW\informe.html`.

> La carpeta que el Explorador llama «Documentos» se llama `Documents` en
> el disco: por eso los comandos escriben `%USERPROFILE%\Documents`. En
> PowerShell en lugar del Símbolo del sistema, escriba
> `$HOME\Documents\LogsWoW` en lugar de `%USERPROFILE%\Documents\LogsWoW`.

---

## Linux (Linux Mint, Ubuntu, Debian, Fedora, Arch, openSUSE…)

### 1. Python

Python 3 ya está instalado en Linux Mint, Ubuntu, Debian (escritorio),
Fedora y openSUSE. Compruébelo en un terminal:

```
python3 --version
```

Si falta:

| Distribución | Comando |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S python` |
| openSUSE | `sudo zypper install python3` |

### 2. La ventana (una vez)

La ventana usa Tkinter, que forma parte de Python pero que la mayoría de
las distribuciones instalan aparte:

| Distribución | Comando |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-tk` |

Sin él, los comandos del terminal siguen funcionando.

### 3. Obtener y ejecutar LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Descargas/logswow-0.10.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.10.0.pyz
```

(En un sistema en inglés, la carpeta es `~/Downloads`.)

Se abre la ventana: lista los registros que ha encontrado, también en un
segundo disco (`/mnt`, `/media`), y «Elegir otro archivo…» permite
buscar un registro en otro sitio.

**Para tenerlo en el menú** (Linux Mint: Menú → Juegos → LogsWoW),
cambie primero el nombre del archivo a `logswow.pyz`, para que el acceso
directo siga funcionando tras las actualizaciones, y luego pegue esto en
un terminal:

```
mv ~/LogsWoW/logswow-0.10.0.pyz ~/LogsWoW/logswow.pyz
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/logswow.desktop <<END
[Desktop Entry]
Type=Application
Name=LogsWoW
Comment=Leer sus registros de combate de World of Warcraft, en local
Exec=python3 $HOME/LogsWoW/logswow.pyz
Terminal=false
Categories=Game;
END
```

Los comandos siguen disponibles en el terminal (si cambió el nombre del
archivo, escriba `logswow.pyz` en lugar de `logswow-0.10.0.pyz`):

```
python3 ~/LogsWoW/logswow-0.10.0.pyz where
```

El archivo también puede ejecutarse directamente, como un comando:

```
chmod +x ~/LogsWoW/logswow-0.10.0.pyz
~/LogsWoW/logswow-0.10.0.pyz where
```

Para no tener que escribir la ruta, añada al final de `~/.bashrc`:

```
alias logswow='python3 ~/LogsWoW/logswow-0.10.0.pyz'
```

y abra un terminal nuevo: `logswow where`, `logswow report …`.

### 4. Dónde está el registro en Linux

El juego funciona en una capa de compatibilidad con Windows, y cada
lanzador guarda su propia copia de la unidad C:. `where` busca en todas
ellas:

| Lanzador | Carpeta `Logs` |
|---|---|
| Lutris (instalador de Battle.net) | `~/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Lutris (instalador de World of Warcraft) | `~/Games/world-of-warcraft/drive_c/…/_retail_/Logs` |
| Steam, con Battle.net añadido como juego ajeno a Steam (Proton) | `~/.steam/steam/steamapps/compatdata/<número>/pfx/drive_c/…/_retail_/Logs` |
| Steam en Flatpak | `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/<número>/pfx/drive_c/…` |
| Bottles (Flatpak) | `~/.var/app/com.usebottles.bottles/data/bottles/bottles/<nombre>/drive_c/…/_retail_/Logs` |
| Wine solo | `~/.wine/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Juego en un segundo disco | `/mnt/<disco>/World of Warcraft/_retail_/Logs`, o bajo `/media/…` y `/run/media/…` (también una o dos carpetas más abajo) |

Si `where` no encuentra nada, busque el archivo usted mismo:

```
find ~ -name 'WoWCombatLog*.txt' 2>/dev/null
```

Ponga la ruta entre comillas: contiene espacios.

```
python3 ~/LogsWoW/logswow-0.10.0.pyz report "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
xdg-open "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

---

## macOS

World of Warcraft es nativo en Mac y se instala en
`/Applications/World of Warcraft`. LogsWoW aún no se ha probado nunca en
un Mac de verdad: solo usa lo que todos los sistemas tienen en común, y
`where` conoce esa ubicación, pero comunique cualquier diferencia.

### 1. Python

Abra el Terminal (Aplicaciones → Utilidades → Terminal) y escriba:

```
python3 --version
```

Si macOS propone instalar las «herramientas de desarrollo de línea de
comandos», acepte: contienen Python 3. Para la ventana, es preferible el
instalador de macOS de python.org, que incluye un Tkinter reciente (con
Homebrew: `brew install python-tk`).

### 2. Obtener y ejecutar LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.10.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.10.0.pyz
```

Se abre la ventana. Para los comandos, en el mismo Terminal:

```
python3 ~/LogsWoW/logswow-0.10.0.pyz where
python3 ~/LogsWoW/logswow-0.10.0.pyz report "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
open "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

Si la carpeta del juego no permite escribir, escriba la página en otro
sitio con `-o ~/Documents/informe.html`.

---

## Desde el código fuente (todos los sistemas)

Para leer el código o ejecutar las pruebas, descargue el ZIP del
repositorio (o `git clone`), entre **en la carpeta que contiene
`logswow`** y sustituya `logswow-0.10.0.pyz` por `-m logswow`:

```
python3 -m logswow where              # Linux, macOS
py -m logswow where                   # Windows
python3 tests/run-tests.py            # las pruebas, sin red
```

Para construir usted mismo el archivo único: `python3 tools/build-pyz`,
que lo escribe en `dist/`.

---

## Comprobar el archivo descargado

Cada versión publica, junto al `.pyz`, un archivo `SHA256SUMS` con su
huella. Para asegurarse de que su archivo es el publicado, calcule la
suya y compárelas:

| Sistema | Comando |
|---|---|
| Windows | `certutil -hashfile logswow-0.10.0.pyz SHA256` |
| Linux | `sha256sum logswow-0.10.0.pyz` |
| macOS | `shasum -a 256 logswow-0.10.0.pyz` |

---

## Actualizar, desinstalar

- **Actualizar**: descargue el nuevo `.pyz` y borre el antiguo. Si creó
  la entrada de menú en Linux, cambie el nombre del nuevo a
  `logswow.pyz` en lugar del antiguo: el acceso directo lo seguirá.
- **Desinstalar**: borre el archivo `.pyz` (o la carpeta del código
  fuente). LogsWoW no escribe nada más en su equipo que los informes HTML
  que usted le pide: ninguna configuración, ninguna caché, ninguna
  entrada del sistema.

---

## Si algo va mal

- **La ventana no se abre, y el terminal menciona Tkinter**: instale el
  paquete que indica (en Linux Mint: `sudo apt install python3-tk`).
- **Ejecute primero `diagnose`**:
  `python3 logswow-0.10.0.pyz diagnose "ruta/del/registro.txt"`. Muestra
  lo que el lector ha entendido del archivo; la línea que importa es
  `PROBLEMAS DE LECTURA: 0`.
- **«No se ha encontrado ningún combate»**: el archivo está vacío, o
  `/combatlog` no estaba activado durante el combate.
- **Las curvas de salud están vacías**: el registro de combate avanzado
  no estaba marcado.
- **Un informe enorme**: una tarde entera ocupa varios megabytes. `list`
  numera los combates, y `report … --only 5` conserva uno solo;
  `--sans-sequence` omite el orden de hechizos y reduce la página más o
  menos a la mitad. `--format pages` escribe una carpeta con una página
  por combate, más ligera de abrir.
