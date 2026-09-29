# LogsWoW installieren und starten

*Version française : [INSTALL.md](INSTALL.md) · English version: [INSTALL.en.md](INSTALL.en.md) · Versión en español: [INSTALL.es.md](INSTALL.es.md)*

LogsWoW braucht nur **Python 3.8 oder neuer**. Sonst ist nichts zu
installieren: keine Bibliothek, kein Konto, keine Verbindung. Es gibt
zwei Wege, es zu bekommen, und der erste genügt fast immer:

- **Die einzelne Datei `logswow-0.10.0.pyz`**, die jeder veröffentlichten
  Version beiliegt (Seite „Releases“ des Repositorys). Sie ist das ganze
  Programm in einer Datei von etwa 170 KB, die so, wie sie ist, aus
  jedem Ordner läuft.
- **Der Quellcode** (Schaltfläche „Code“, dann „Download ZIP“, oder
  `git clone`), für alle, die den Code lesen oder die Tests ausführen
  möchten.

Das Repository ist öffentlich: Zum Herunterladen ist kein Konto nötig.
Sie können die `.pyz`-Datei auch einfach weitergeben: Mehr braucht es
nicht.

Ersetzen Sie in den Beispielen unten `0.10.0` durch die Nummer der
Version, die Sie heruntergeladen haben.

LogsWoW spricht die Sprache Ihres Rechners, wenn es sie kennt (Deutsch,
Englisch, Französisch, Spanisch), sonst Englisch. Fügen Sie einem Befehl
`--langue de` hinzu, um Deutsch zu erzwingen, oder legen Sie es mit der
Umgebungsvariable `LOGSWOW_LANGUE=de` dauerhaft fest.

---

## Zuerst im Spiel (einmalig)

1. **Erweiterte Kampfprotokollierung**: System → Netzwerk → „Erweiterte
   Kampfprotokollierung“ anhaken. Die Einstellung bleibt von einer
   Sitzung zur nächsten erhalten. Ohne sie enthält die Datei weder
   Lebenspunkte noch Positionen, und mehrere Kurven des Berichts bleiben
   leer.
2. **`/combatlog`** im Chatfenster, zu Beginn jeder Spielsitzung, um die
   Aufzeichnung zu starten. Das bleibt nicht bestehen: Tippen Sie es bei
   jeder Anmeldung erneut (oder verwenden Sie ein kleines Addon, das es
   beim Betreten einer Instanz erledigt).

Das Spiel schreibt dann `WoWCombatLog-<Datum>.txt` in seinen Ordner
`Logs`.

---

## Windows 10 und 11

### 1. Python installieren

1. Laden Sie den Windows-Installer von **python.org** herunter
   („Downloads“, Version 3.12 oder neuer).
2. Setzen Sie auf dem ersten Bildschirm des Installers **den Haken bei
   „Add python.exe to PATH“**, dann „Install Now“.
3. Prüfen: Öffnen Sie die Eingabeaufforderung (Windows-Taste, `cmd`
   tippen, Eingabe) und tippen Sie:

   ```
   py --version
   ```

   Es sollte eine Zeile `Python 3.x.y` erscheinen.

> Wenn das Tippen von `python` den Microsoft Store öffnet, statt zu
> antworten, ist das eine Verknüpfung von Windows, nicht Python:
> Verwenden Sie `py`, das python.org installiert, oder schalten Sie die
> Verknüpfung unter Einstellungen → Apps → Erweiterte App-Einstellungen →
> App-Ausführungsaliase ab.

### 2. LogsWoW holen

Laden Sie `logswow-0.10.0.pyz` herunter und legen Sie es ab, wo Sie
möchten, zum Beispiel in `Dokumente\LogsWoW`.

### 3. Starten

**Doppelklicken Sie auf `logswow-0.10.0.pyz`**: Das Fenster von LogsWoW
öffnet sich. Es listet die gefundenen Protokolle auf (auf den Laufwerken
C: bis H:), Sie wählen eines, dann die Kämpfe, und „Bericht erstellen
und öffnen“ zeigt die Seite in Ihrem Browser.

Dahinter öffnet sich auch ein schwarzes Fenster: Das ist normal. Um es
nicht mehr zu sehen, benennen Sie die Datei in `logswow-0.10.0.pyzw` um
(mit einem **w** am Ende); um sie auf dem Desktop zu haben: Rechtsklick
→ Senden an → Desktop (Verknüpfung erstellen).

Wenn der Doppelklick nichts startet, oder um die Befehle zu verwenden:
Wechseln Sie in der Eingabeaufforderung in diesen Ordner, dann:

```
cd %USERPROFILE%\Documents\LogsWoW
py logswow-0.10.0.pyz where
```

`where` zeigt den Ordner `Logs` des Spiels (es sucht auf den Laufwerken
C: bis H:) und die neuesten Protokolle darin. Dann:

```
py logswow-0.10.0.pyz report "C:\Program Files (x86)\World of Warcraft\_retail_\Logs\WoWCombatLog-091826_203000.txt"
```

Die HTML-Seite (mit Registerkarten aufgebaut; `--format pages` oder
`--format longue` für die anderen Darstellungen) erscheint neben dem
Protokoll, unter demselben Namen mit der Endung `.html`; ein
Doppelklick öffnet sie in Ihrem Browser. Um sie anderswo zu schreiben,
fügen Sie zum Beispiel
`-o %USERPROFILE%\Documents\LogsWoW\bericht.html` hinzu.

> Der Ordner, den der Explorer „Dokumente“ nennt, heißt auf der
> Festplatte `Documents`: Deshalb steht in den Befehlen
> `%USERPROFILE%\Documents`. In PowerShell statt der
> Eingabeaufforderung schreiben Sie `$HOME\Documents\LogsWoW` statt
> `%USERPROFILE%\Documents\LogsWoW`.

---

## Linux (Linux Mint, Ubuntu, Debian, Fedora, Arch, openSUSE…)

### 1. Python

Python 3 ist unter Linux Mint, Ubuntu, Debian (Desktop), Fedora und
openSUSE bereits installiert. Prüfen Sie in einem Terminal:

```
python3 --version
```

Falls es fehlt:

| Distribution | Befehl |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S python` |
| openSUSE | `sudo zypper install python3` |

### 2. Das Fenster (einmalig)

Das Fenster verwendet Tkinter, das zu Python gehört, das die meisten
Distributionen aber getrennt ausliefern:

| Distribution | Befehl |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-tk` |

Ohne es funktionieren die Befehle im Terminal trotzdem.

### 3. LogsWoW holen und starten

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.10.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.10.0.pyz
```

Das Fenster öffnet sich: Es listet die gefundenen Protokolle auf, auch
auf einer zweiten Festplatte (`/mnt`, `/media`), und „Andere Datei
wählen…“ holt ein Protokoll von anderswo.

**Um es im Menü zu haben** (Linux Mint: Menü → Spiele → LogsWoW),
benennen Sie die Datei zuerst in `logswow.pyz` um, damit die
Verknüpfung nach Aktualisierungen weiter funktioniert, und fügen Sie
dann dies in ein Terminal ein:

```
mv ~/LogsWoW/logswow-0.10.0.pyz ~/LogsWoW/logswow.pyz
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/logswow.desktop <<END
[Desktop Entry]
Type=Application
Name=LogsWoW
Comment=Die eigenen Kampfprotokolle von World of Warcraft lesen, lokal
Exec=python3 $HOME/LogsWoW/logswow.pyz
Terminal=false
Categories=Game;
END
```

Die Befehle bleiben im Terminal verfügbar (wenn Sie die Datei umbenannt
haben, schreiben Sie `logswow.pyz` statt `logswow-0.10.0.pyz`):

```
python3 ~/LogsWoW/logswow-0.10.0.pyz where
```

Die Datei kann auch direkt laufen, wie ein Befehl:

```
chmod +x ~/LogsWoW/logswow-0.10.0.pyz
~/LogsWoW/logswow-0.10.0.pyz where
```

Um den Pfad nicht mehr tippen zu müssen, fügen Sie am Ende von
`~/.bashrc` hinzu:

```
alias logswow='python3 ~/LogsWoW/logswow-0.10.0.pyz'
```

und öffnen Sie dann ein neues Terminal: `logswow where`,
`logswow report …`.

### 4. Wo das Protokoll unter Linux liegt

Das Spiel läuft in einer Windows-Kompatibilitätsschicht, und jeder
Launcher hat seine eigene Kopie von Laufwerk C:. `where` sucht in all
diesen:

| Launcher | Ordner `Logs` |
|---|---|
| Lutris (Battle.net-Installer) | `~/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Lutris (World-of-Warcraft-Installer) | `~/Games/world-of-warcraft/drive_c/…/_retail_/Logs` |
| Steam, mit Battle.net als Nicht-Steam-Spiel (Proton) | `~/.steam/steam/steamapps/compatdata/<Nummer>/pfx/drive_c/…/_retail_/Logs` |
| Steam als Flatpak | `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/<Nummer>/pfx/drive_c/…` |
| Bottles (Flatpak) | `~/.var/app/com.usebottles.bottles/data/bottles/bottles/<Name>/drive_c/…/_retail_/Logs` |
| Wine allein | `~/.wine/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Spiel auf einer zweiten Festplatte | `/mnt/<Festplatte>/World of Warcraft/_retail_/Logs`, oder unter `/media/…` und `/run/media/…` (auch ein oder zwei Ordner tiefer) |

Wenn `where` nichts findet, suchen Sie die Datei selbst:

```
find ~ -name 'WoWCombatLog*.txt' 2>/dev/null
```

Setzen Sie den Pfad in Anführungszeichen: Er enthält Leerzeichen.

```
python3 ~/LogsWoW/logswow-0.10.0.pyz report "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
xdg-open "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

---

## macOS

World of Warcraft läuft nativ auf dem Mac und wird unter
`/Applications/World of Warcraft` installiert. LogsWoW wurde noch nie
auf einem echten Mac ausprobiert: Es verwendet nur, was alle Systeme
gemeinsam haben, und `where` kennt diesen Ort, aber bitte melden Sie
alles, was abweicht.

### 1. Python

Öffnen Sie das Terminal (Programme → Dienstprogramme → Terminal) und
tippen Sie:

```
python3 --version
```

Wenn macOS anbietet, die „Befehlszeilenentwicklerwerkzeuge“ zu
installieren, nehmen Sie an: Sie enthalten Python 3. Für das Fenster
ist der macOS-Installer von python.org vorzuziehen, der ein aktuelles
Tkinter mitbringt (mit Homebrew: `brew install python-tk`).

### 2. LogsWoW holen und starten

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.10.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.10.0.pyz
```

Das Fenster öffnet sich. Für die Befehle, im selben Terminal:

```
python3 ~/LogsWoW/logswow-0.10.0.pyz where
python3 ~/LogsWoW/logswow-0.10.0.pyz report "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
open "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

Wenn der Ordner des Spiels das Schreiben verweigert, schreiben Sie die
Seite anderswohin, mit `-o ~/Documents/bericht.html`.

---

## Aus dem Quellcode (alle Systeme)

Um den Code zu lesen oder die Tests auszuführen, laden Sie das ZIP des
Repositorys herunter (oder `git clone`), wechseln Sie **in den Ordner,
der `logswow` enthält**, und ersetzen Sie `logswow-0.10.0.pyz` durch
`-m logswow`:

```
python3 -m logswow where              # Linux, macOS
py -m logswow where                   # Windows
python3 tests/run-tests.py            # die Tests, ohne Netzwerk
```

Um die einzelne Datei selbst zu bauen: `python3 tools/build-pyz`, das
sie in `dist/` schreibt.

---

## Die heruntergeladene Datei prüfen

Jede Version veröffentlicht neben der `.pyz` eine Datei `SHA256SUMS`
mit ihrem Fingerabdruck. Um sicherzugehen, dass Ihre Datei die
veröffentlichte ist, berechnen Sie den Ihren und vergleichen Sie:

| System | Befehl |
|---|---|
| Windows | `certutil -hashfile logswow-0.10.0.pyz SHA256` |
| Linux | `sha256sum logswow-0.10.0.pyz` |
| macOS | `shasum -a 256 logswow-0.10.0.pyz` |

---

## Aktualisieren, deinstallieren

- **Aktualisieren**: Laden Sie die neue `.pyz` herunter und löschen Sie
  die alte. Wenn Sie unter Linux den Menüeintrag angelegt haben,
  benennen Sie die neue in `logswow.pyz` um, anstelle der alten: Die
  Verknüpfung folgt.
- **Deinstallieren**: Löschen Sie die `.pyz`-Datei (oder den Ordner des
  Quellcodes). LogsWoW schreibt nichts anderes auf Ihren Rechner als die
  HTML-Berichte, die Sie anfordern: keine Konfiguration, kein
  Zwischenspeicher, kein Systemeintrag.

---

## Wenn etwas schiefgeht

- **Das Fenster öffnet sich nicht, und das Terminal erwähnt Tkinter**:
  Installieren Sie das genannte Paket (unter Linux Mint:
  `sudo apt install python3-tk`).
- **Führen Sie zuerst `diagnose` aus**:
  `python3 logswow-0.10.0.pyz diagnose "Pfad/zum/Protokoll.txt"`. Es
  zeigt, was das Programm von der Datei verstanden hat; die Zeile, auf
  die es ankommt, ist `LESEPROBLEME: 0`.
- **„Kein Kampf gefunden“**: Die Datei ist leer, oder `/combatlog` lief
  während des Kampfes nicht.
- **Die Lebenskurven sind leer**: Die erweiterte Kampfprotokollierung
  war nicht angehakt.
- **Ein riesiger Bericht**: Ein ganzer Abend ergibt mehrere Megabyte.
  `list` nummeriert die Kämpfe, und `report … --only 5` behält nur
  einen; `--sans-sequence` lässt die Zauberreihenfolge weg und halbiert
  die Seite ungefähr. `--format pages` schreibt einen Ordner mit einer
  Seite pro Kampf, leichter zu öffnen.
