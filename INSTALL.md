# Installer et lancer LogsWoW

LogsWoW n'a besoin que de **Python 3.8 ou plus récent**. Rien d'autre à
installer : pas de bibliothèque, pas de compte, pas de connexion. Il
existe deux façons de le récupérer, et la première suffit presque
toujours :

- **Le fichier unique `logswow-0.3.1.pyz`**, joint à chaque version
  publiée (page « Releases » du dépôt). C'est tout le programme en un
  fichier de 90 Ko, qu'on lance tel quel depuis n'importe quel dossier.
- **Le code source** (bouton « Code » puis « Download ZIP », ou
  `git clone`), pour qui veut lire le code ou lancer les tests.

Le dépôt est privé : pour télécharger, il faut un compte GitHub à qui le
propriétaire a donné accès. Sinon, qu'il vous transmette simplement le
fichier `.pyz` : il n'en faut pas plus.

Dans les exemples ci-dessous, remplacez `0.3.1` par le numéro de la
version que vous avez téléchargée.

---

## Avant tout, côté jeu (une seule fois)

1. **Journalisation de combat avancée** : Système → Réseau → cochez
   « Journalisation de combat avancée ». Le réglage reste d'une session à
   l'autre. Sans lui, le fichier ne contient ni points de vie ni
   positions, et plusieurs courbes du rapport restent vides.
2. **`/combatlog`** dans la fenêtre de discussion, au début de chaque
   session de jeu, pour lancer l'enregistrement. Ce réglage-là ne dure
   pas : il faut le retaper à chaque connexion (ou utiliser un petit
   addon qui le fait en entrant dans une instance).

Le jeu écrit alors `WoWCombatLog-<date>.txt` dans son dossier `Logs`.

---

## Windows 10 et 11

### 1. Installer Python

1. Téléchargez l'installateur Windows sur **python.org** (« Downloads »,
   version 3.12 ou plus récente).
2. Au premier écran de l'installateur, **cochez « Add python.exe to
   PATH »**, puis « Install Now ».
3. Vérifiez : ouvrez l'Invite de commandes (touche Windows, tapez `cmd`,
   Entrée) et tapez :

   ```
   py --version
   ```

   Une ligne `Python 3.x.y` doit s'afficher.

> Si taper `python` ouvre le Microsoft Store au lieu de répondre, c'est
> un raccourci de Windows, pas Python : utilisez `py`, qu'installe
> python.org, ou désactivez le raccourci dans Paramètres → Applications
> → Paramètres avancés des applications → Alias d'exécution
> d'application.

### 2. Récupérer LogsWoW

Téléchargez `logswow-0.3.1.pyz` et rangez-le où vous voulez, par
exemple dans `Documents\LogsWoW`.

### 3. Le lancer

Dans l'Invite de commandes, placez-vous dans ce dossier, puis :

```
cd %USERPROFILE%\Documents\LogsWoW
py logswow-0.3.1.pyz where
```

`where` affiche le dossier `Logs` du jeu (il regarde sur les disques C:
à H:) et les derniers journaux qu'il contient. Ensuite :

```
py logswow-0.3.1.pyz report "C:\Program Files (x86)\World of Warcraft\_retail_\Logs\WoWCombatLog-091826_203000.txt"
```

La page HTML apparaît à côté du journal, sous le même nom en `.html` ;
double-cliquez dessus pour l'ouvrir dans votre navigateur. Pour l'écrire
ailleurs, ajoutez par exemple
`-o %USERPROFILE%\Documents\LogsWoW\rapport.html`.

> Dans PowerShell plutôt que l'Invite de commandes, écrivez
> `$HOME\Documents\LogsWoW` à la place de `%USERPROFILE%\Documents\LogsWoW`.

---

## Linux (Linux Mint, Ubuntu, Debian, Fedora, Arch, openSUSE…)

### 1. Python

Python 3 est déjà installé sur Linux Mint, Ubuntu, Debian (bureau),
Fedora et openSUSE. Vérifiez dans un terminal :

```
python3 --version
```

S'il manque :

| Distribution | Commande |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S python` |
| openSUSE | `sudo zypper install python3` |

### 2. Récupérer et lancer LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Téléchargements/logswow-0.3.1.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.3.1.pyz where
```

(Sur un système en anglais, le dossier est `~/Downloads`.)

Le fichier peut aussi se lancer directement, comme une commande :

```
chmod +x ~/LogsWoW/logswow-0.3.1.pyz
~/LogsWoW/logswow-0.3.1.pyz where
```

Pour ne plus taper le chemin, ajoutez à la fin de `~/.bashrc` :

```
alias logswow='python3 ~/LogsWoW/logswow-0.3.1.pyz'
```

puis ouvrez un nouveau terminal : `logswow where`, `logswow report …`.

### 3. Où est le journal sous Linux

Le jeu tourne dans une couche de compatibilité Windows, et chaque
lanceur garde sa propre copie du disque C:. `where` regarde dans toutes
celles-ci :

| Lanceur | Dossier `Logs` |
|---|---|
| Lutris (installateur Battle.net) | `~/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |
| Lutris (installateur World of Warcraft) | `~/Games/world-of-warcraft/drive_c/…/_retail_/Logs` |
| Steam, avec Battle.net ajouté comme jeu non-Steam (Proton) | `~/.steam/steam/steamapps/compatdata/<numéro>/pfx/drive_c/…/_retail_/Logs` |
| Steam en Flatpak | `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/<numéro>/pfx/drive_c/…` |
| Bottles (Flatpak) | `~/.var/app/com.usebottles.bottles/data/bottles/bottles/<nom>/drive_c/…/_retail_/Logs` |
| Wine seul | `~/.wine/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs` |

Si `where` ne trouve rien, cherchez le fichier vous-même :

```
find ~ -name 'WoWCombatLog*.txt' 2>/dev/null
```

Mettez le chemin entre guillemets : il contient des espaces.

```
python3 ~/LogsWoW/logswow-0.3.1.pyz report "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
xdg-open "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

---

## macOS

World of Warcraft est natif sur Mac et s'installe dans
`/Applications/World of Warcraft`. LogsWoW n'a encore jamais été essayé
sur un vrai Mac : il n'utilise que ce qui est commun à tous les systèmes,
et `where` connaît cet emplacement, mais signalez tout écart.

### 1. Python

Ouvrez le Terminal (Applications → Utilitaires → Terminal) et tapez :

```
python3 --version
```

Si macOS propose d'installer les « outils de ligne de commande pour
développeurs », acceptez : ils contiennent Python 3. Vous pouvez aussi
prendre l'installateur macOS sur python.org.

### 2. Récupérer et lancer LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.3.1.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.3.1.pyz where
python3 ~/LogsWoW/logswow-0.3.1.pyz report "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
open "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

Si le dossier du jeu refuse l'écriture, écrivez la page ailleurs avec
`-o ~/Documents/rapport.html`.

---

## Depuis le code source (tous systèmes)

Pour lire le code ou lancer les tests, téléchargez le ZIP du dépôt (ou
`git clone`), placez-vous **dans le dossier qui contient `logswow`**, et
remplacez `logswow-0.3.1.pyz` par `-m logswow` :

```
python3 -m logswow where              # Linux, macOS
py -m logswow where                   # Windows
python3 tests/run-tests.py            # les tests, sans réseau
```

Pour fabriquer vous-même le fichier unique : `python3 tools/build-pyz`,
qui l'écrit dans `dist/`.

---

## Vérifier le fichier téléchargé

Chaque version publie à côté du `.pyz` un fichier `SHA256SUMS` qui donne
son empreinte. Pour vous assurer que le fichier est bien celui qui a été
publié, calculez la vôtre et comparez :

| Système | Commande |
|---|---|
| Windows | `certutil -hashfile logswow-0.3.1.pyz SHA256` |
| Linux | `sha256sum logswow-0.3.1.pyz` |
| macOS | `shasum -a 256 logswow-0.3.1.pyz` |

---

## Mettre à jour, désinstaller

- **Mettre à jour** : téléchargez le nouveau `.pyz` et supprimez l'ancien.
- **Désinstaller** : supprimez le fichier `.pyz` (ou le dossier du code
  source). LogsWoW n'écrit rien d'autre sur votre machine que les
  rapports HTML que vous lui demandez : aucune configuration, aucun
  cache, aucune entrée dans le système.

---

## Si quelque chose ne va pas

- **Lancez `diagnose` en premier** :
  `python3 logswow-0.3.1.pyz diagnose "chemin/du/journal.txt"`. Il montre
  ce que le lecteur a compris du fichier ; la ligne qui compte est
  `PROBLEMES DE LECTURE : 0`.
- **« Aucun combat n'a été trouvé »** : le fichier est vide, ou
  `/combatlog` n'était pas lancé pendant le combat.
- **Les courbes de vie sont vides** : la journalisation de combat avancée
  n'était pas cochée.
- **Un rapport énorme** : une soirée entière fait plusieurs mégaoctets.
  `list` numérote les combats, et `report … --only 5` n'en garde qu'un ;
  `--sans-sequence` retire l'ordre des sorts et divise la page par deux
  environ.
