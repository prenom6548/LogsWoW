# Installing and running LogsWoW

*Version française : [INSTALL.md](INSTALL.md)*

LogsWoW needs only **Python 3.8 or newer**. Nothing else to install: no
library, no account, no connection. There are two ways to get it, and
the first is almost always enough:

- **The single file `logswow-0.9.0.pyz`**, attached to every published
  version (the repository's "Releases" page). It is the whole program in
  one file of about 140 KB, which runs as it is from any folder.
- **The source code** ("Code" button then "Download ZIP", or
  `git clone`), for those who want to read the code or run the tests.

The repository is public: no account is needed to download. You can
also simply pass the `.pyz` file around: nothing more is needed.

In the examples below, replace `0.9.0` with the number of the version
you downloaded.

LogsWoW speaks your machine's language: French on a French machine,
English on every other. Add `--langue en` to a command to force English,
or set it once and for all with the environment variable
`LOGSWOW_LANGUE=en`.

---

## First, in the game (once)

1. **Advanced combat logging**: System → Network → tick "Advanced Combat
   Logging". The setting carries over from one session to the next.
   Without it the file holds neither health nor positions, and several
   of the report's curves stay empty.
2. **`/combatlog`** in the chat window, at the start of every game
   session, to start recording. This one does not last: type it again at
   every login (or use a small addon that does it when entering an
   instance).

The game then writes `WoWCombatLog-<date>.txt` in its `Logs` folder.

---

## Windows 10 and 11

### 1. Install Python

1. Download the Windows installer from **python.org** ("Downloads",
   version 3.12 or newer).
2. On the installer's first screen, **tick "Add python.exe to PATH"**,
   then "Install Now".
3. Check: open the Command Prompt (Windows key, type `cmd`, Enter) and
   type:

   ```
   py --version
   ```

   A line `Python 3.x.y` should appear.

> If typing `python` opens the Microsoft Store instead of answering, that
> is a Windows shortcut, not Python: use `py`, which python.org installs,
> or turn the shortcut off in Settings → Apps → Advanced app settings →
> App execution aliases.

### 2. Get LogsWoW

Download `logswow-0.9.0.pyz` and put it wherever you like, for instance
in `Documents\LogsWoW`.

### 3. Run it

**Double-click `logswow-0.9.0.pyz`**: the LogsWoW window opens. It lists
the logs it found (on drives C: to H:), you choose one, then the fights,
and "Create the report and open it" shows the page in your browser.

A black window also opens behind it: that is normal. To stop seeing it,
rename the file to `logswow-0.9.0.pyzw` (with a **w** at the end); to
have it on the desktop, right-click → Send to → Desktop (create
shortcut).

If the double-click starts nothing, or to use the commands: in the
Command Prompt, go to that folder, then:

```
cd %USERPROFILE%\Documents\LogsWoW
py logswow-0.9.0.pyz where
```

`where` shows the game's `Logs` folder (it looks on drives C: to H:) and
the latest logs in it. Then:

```
py logswow-0.9.0.pyz report "C:\Program Files (x86)\World of Warcraft\_retail_\Logs\WoWCombatLog-091826_203000.txt"
```

The HTML page (laid out in tabs; `--format pages` or `--format longue`
for the other layouts) appears next to the log, under the same name
ending in `.html`; double-click it to open it in your browser. To write
it elsewhere, add for instance
`-o %USERPROFILE%\Documents\LogsWoW\report.html`.

> In PowerShell rather than the Command Prompt, write
> `$HOME\Documents\LogsWoW` instead of `%USERPROFILE%\Documents\LogsWoW`.

---

## Linux (Linux Mint, Ubuntu, Debian, Fedora, Arch, openSUSE…)

### 1. Python

Python 3 is already installed on Linux Mint, Ubuntu, Debian (desktop),
Fedora and openSUSE. Check in a terminal:

```
python3 --version
```

If it is missing:

| Distribution | Command |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S python` |
| openSUSE | `sudo zypper install python3` |

### 2. The window (once)

The window uses Tkinter, which is part of Python but which most
distributions ship separately:

| Distribution | Command |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-tk` |

Without it, the terminal commands still work.

### 3. Get and run LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.9.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.9.0.pyz
```

(On a system in French, the folder is `~/Téléchargements`.)

The window opens: it lists the logs it found, including on a second disk
(`/mnt`, `/media`), and "Choose another file…" lets you fetch a log from
elsewhere.

**To have it in the menu** (Linux Mint: Menu → Games → LogsWoW), first
rename the file `logswow.pyz`, so that the shortcut still works after
updates, then paste this into a terminal:

```
mv ~/LogsWoW/logswow-0.9.0.pyz ~/LogsWoW/logswow.pyz
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/logswow.desktop <<END
[Desktop Entry]
Type=Application
Name=LogsWoW
Comment=Read your World of Warcraft combat logs, locally
Exec=python3 $HOME/LogsWoW/logswow.pyz
Terminal=false
Categories=Game;
END
```

The commands stay available in the terminal (if you renamed the file,
write `logswow.pyz` instead of `logswow-0.9.0.pyz`):

```
python3 ~/LogsWoW/logswow-0.9.0.pyz where
```

The file can also run directly, like a command:

```
chmod +x ~/LogsWoW/logswow-0.9.0.pyz
~/LogsWoW/logswow-0.9.0.pyz where
```

To stop typing the path, add at the end of `~/.bashrc`:

```
alias logswow='python3 ~/LogsWoW/logswow-0.9.0.pyz'
```

then open a new terminal: `logswow where`, `logswow report …`.

### 4. Where the log is on Linux

The game runs in a Windows compatibility layer, and each launcher keeps
its own copy of drive C:. `where` looks in all of these:

| Launcher | `Logs` folder |
|---|---|
| Lutris (Battle.net installer) | `~/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Lutris (World of Warcraft installer) | `~/Games/world-of-warcraft/drive_c/…/_retail_/Logs` |
| Steam, with Battle.net added as a non-Steam game (Proton) | `~/.steam/steam/steamapps/compatdata/<number>/pfx/drive_c/…/_retail_/Logs` |
| Steam as a Flatpak | `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/<number>/pfx/drive_c/…` |
| Bottles (Flatpak) | `~/.var/app/com.usebottles.bottles/data/bottles/bottles/<name>/drive_c/…/_retail_/Logs` |
| Wine alone | `~/.wine/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Game on a second disk | `/mnt/<disk>/World of Warcraft/_retail_/Logs`, or under `/media/…` and `/run/media/…` (one or two folders down too) |

If `where` finds nothing, look for the file yourself:

```
find ~ -name 'WoWCombatLog*.txt' 2>/dev/null
```

Put the path in quotes: it contains spaces.

```
python3 ~/LogsWoW/logswow-0.9.0.pyz report "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
xdg-open "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

---

## macOS

World of Warcraft is native on Mac and installs in
`/Applications/World of Warcraft`. LogsWoW has never been tried on a
real Mac yet: it uses only what all systems share, and `where` knows
that location, but please report anything that differs.

### 1. Python

Open the Terminal (Applications → Utilities → Terminal) and type:

```
python3 --version
```

If macOS offers to install the "command line developer tools", accept:
they contain Python 3. For the window, prefer the python.org macOS
installer, which provides a recent Tkinter (with Homebrew:
`brew install python-tk`).

### 2. Get and run LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.9.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.9.0.pyz
```

The window opens. For the commands, in the same Terminal:

```
python3 ~/LogsWoW/logswow-0.9.0.pyz where
python3 ~/LogsWoW/logswow-0.9.0.pyz report "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
open "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

If the game's folder refuses writing, write the page elsewhere with
`-o ~/Documents/report.html`.

---

## From the source code (all systems)

To read the code or run the tests, download the repository's ZIP (or
`git clone`), go **into the folder that contains `logswow`**, and
replace `logswow-0.9.0.pyz` with `-m logswow`:

```
python3 -m logswow where              # Linux, macOS
py -m logswow where                   # Windows
python3 tests/run-tests.py            # the tests, no network
```

To build the single file yourself: `python3 tools/build-pyz`, which
writes it into `dist/`.

---

## Checking the downloaded file

Every version publishes, next to the `.pyz`, a `SHA256SUMS` file giving
its fingerprint. To make sure your file is the one that was published,
compute yours and compare:

| System | Command |
|---|---|
| Windows | `certutil -hashfile logswow-0.9.0.pyz SHA256` |
| Linux | `sha256sum logswow-0.9.0.pyz` |
| macOS | `shasum -a 256 logswow-0.9.0.pyz` |

---

## Updating, uninstalling

- **Updating**: download the new `.pyz` and delete the old one. If you
  created the menu entry on Linux, rename the new one `logswow.pyz` in
  place of the old one: the shortcut will follow.
- **Uninstalling**: delete the `.pyz` file (or the source code folder).
  LogsWoW writes nothing else on your machine than the HTML reports you
  ask it for: no configuration, no cache, no system entry.

---

## If something goes wrong

- **The window does not open, and the terminal mentions Tkinter**:
  install the package it names (on Linux Mint: `sudo apt install python3-tk`).
- **Run `diagnose` first**:
  `python3 logswow-0.9.0.pyz diagnose "path/to/the/log.txt"`. It shows
  what the reader understood of the file; the line that matters is
  `READ PROBLEMS: 0`.
- **"No fight was found"**: the file is empty, or `/combatlog` was not
  running during the fight.
- **The health curves are empty**: advanced combat logging was not
  ticked.
- **A huge report**: a whole evening makes several megabytes. `list`
  numbers the fights, and `report … --only 5` keeps just one;
  `--sans-sequence` leaves out the cast order and roughly halves the
  page. `--format pages` writes a folder with one page per fight,
  lighter to open.
