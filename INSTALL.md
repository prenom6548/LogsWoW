# Installer et lancer LogsWoW

LogsWoW n'a besoin que de **Python 3.8 ou plus récent**. Rien d'autre à
installer : pas de bibliothèque, pas de compte, pas de connexion. Il
existe deux façons de le récupérer, et la première suffit presque
toujours :

- **Le fichier unique `logswow-0.7.0.pyz`**, joint à chaque version
  publiée (page « Releases » du dépôt). C'est tout le programme en un
  fichier de 90 Ko, qu'on lance tel quel depuis n'importe quel dossier.
- **Le code source** (bouton « Code » puis « Download ZIP », ou
  `git clone`), pour qui veut lire le code ou lancer les tests.

Le dépôt est privé : pour télécharger, il faut un compte GitHub à qui le
propriétaire a donné accès. Sinon, qu'il vous transmette simplement le
fichier `.pyz` : il n'en faut pas plus.

Dans les exemples ci-dessous, remplacez `0.7.0` par le numéro de la
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

Téléchargez `logswow-0.7.0.pyz` et rangez-le où vous voulez, par
exemple dans `Documents\LogsWoW`.

### 3. Le lancer

**Double-cliquez sur `logswow-0.7.0.pyz`** : la fenêtre de LogsWoW s'ouvre.
Elle liste les journaux trouvés (sur les disques C: à H:), vous en
choisissez un, puis les combats, et « Créer le rapport et l'ouvrir »
affiche la page dans votre navigateur.

Une fenêtre noire s'ouvre aussi derrière elle : c'est normal. Pour ne plus
la voir, renommez le fichier en `logswow-0.7.0.pyzw` (avec un **w** à la
fin) ; pour l'avoir sur le bureau, clic droit → Envoyer vers → Bureau
(créer un raccourci).

Si le double-clic ne lance rien, ou pour utiliser les commandes :
dans l'Invite de commandes, placez-vous dans ce dossier, puis :

```
cd %USERPROFILE%\Documents\LogsWoW
py logswow-0.7.0.pyz where
```

`where` affiche le dossier `Logs` du jeu (il regarde sur les disques C:
à H:) et les derniers journaux qu'il contient. Ensuite :

```
py logswow-0.7.0.pyz report "C:\Program Files (x86)\World of Warcraft\_retail_\Logs\WoWCombatLog-091826_203000.txt"
```

La page HTML (présentée en onglets ; `--format pages` ou `--format longue`
pour les autres présentations) apparaît à côté du journal, sous le même
nom en `.html` ;
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

### 2. La fenêtre (une seule fois)

La fenêtre utilise Tkinter, qui fait partie de Python mais que la plupart
des distributions livrent à part :

| Distribution | Commande |
|---|---|
| Linux Mint, Ubuntu, Debian | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| Arch, Manjaro, EndeavourOS | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-tk` |

Sans elle, les commandes du terminal fonctionnent quand même.

### 3. Récupérer et lancer LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Téléchargements/logswow-0.7.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.7.0.pyz
```

(Sur un système en anglais, le dossier est `~/Downloads`.)

La fenêtre s'ouvre : elle liste les journaux qu'elle a trouvés, y compris
sur un second disque (`/mnt`, `/media`), et « Choisir un autre fichier… »
permet d'aller chercher un journal ailleurs.

**Pour l'avoir dans le menu** (Linux Mint : Menu → Jeux → LogsWoW),
renommez d'abord le fichier `logswow.pyz`, pour que le raccourci serve
encore après les mises à jour, puis collez ceci dans un terminal :

```
mv ~/LogsWoW/logswow-0.7.0.pyz ~/LogsWoW/logswow.pyz
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/logswow.desktop <<FIN
[Desktop Entry]
Type=Application
Name=LogsWoW
Comment=Lire ses journaux de combat de World of Warcraft, en local
Exec=python3 $HOME/LogsWoW/logswow.pyz
Terminal=false
Categories=Game;
FIN
```

Les commandes restent disponibles, dans le terminal (si vous avez renommé
le fichier, écrivez `logswow.pyz` à la place de `logswow-0.7.0.pyz`) :

```
python3 ~/LogsWoW/logswow-0.7.0.pyz where
```

Le fichier peut aussi se lancer directement, comme une commande :

```
chmod +x ~/LogsWoW/logswow-0.7.0.pyz
~/LogsWoW/logswow-0.7.0.pyz where
```

Pour ne plus taper le chemin, ajoutez à la fin de `~/.bashrc` :

```
alias logswow='python3 ~/LogsWoW/logswow-0.7.0.pyz'
```

puis ouvrez un nouveau terminal : `logswow where`, `logswow report …`.

### 4. Où est le journal sous Linux

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
| Jeu sur un second disque | `/mnt/<disque>/World of Warcraft/_retail_/Logs`, ou sous `/media/…` et `/run/media/…` (un ou deux dossiers plus bas aussi) |

Si `where` ne trouve rien, cherchez le fichier vous-même :

```
find ~ -name 'WoWCombatLog*.txt' 2>/dev/null
```

Mettez le chemin entre guillemets : il contient des espaces.

```
python3 ~/LogsWoW/logswow-0.7.0.pyz report "$HOME/Games/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
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
développeurs », acceptez : ils contiennent Python 3. Pour la fenêtre,
préférez l'installateur macOS de python.org, qui fournit une version
récente de Tkinter (avec Homebrew : `brew install python-tk`).

### 2. Récupérer et lancer LogsWoW

```
mkdir -p ~/LogsWoW
mv ~/Downloads/logswow-0.7.0.pyz ~/LogsWoW/
python3 ~/LogsWoW/logswow-0.7.0.pyz
```

La fenêtre s'ouvre. Pour les commandes, dans le même Terminal :

```
python3 ~/LogsWoW/logswow-0.7.0.pyz where
python3 ~/LogsWoW/logswow-0.7.0.pyz report "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.txt"
open "/Applications/World of Warcraft/_retail_/Logs/WoWCombatLog-091826_203000.html"
```

Si le dossier du jeu refuse l'écriture, écrivez la page ailleurs avec
`-o ~/Documents/rapport.html`.

---

## Depuis le code source (tous systèmes)

Pour lire le code ou lancer les tests, téléchargez le ZIP du dépôt (ou
`git clone`), placez-vous **dans le dossier qui contient `logswow`**, et
remplacez `logswow-0.7.0.pyz` par `-m logswow` :

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
| Windows | `certutil -hashfile logswow-0.7.0.pyz SHA256` |
| Linux | `sha256sum logswow-0.7.0.pyz` |
| macOS | `shasum -a 256 logswow-0.7.0.pyz` |

---

## Mettre à jour, désinstaller

- **Mettre à jour** : téléchargez le nouveau `.pyz` et supprimez l'ancien.
  Si vous avez créé l'entrée de menu sous Linux, renommez le nouveau en
  `logswow.pyz` à la place de l'ancien : le raccourci suivra.
- **Désinstaller** : supprimez le fichier `.pyz` (ou le dossier du code
  source). LogsWoW n'écrit rien d'autre sur votre machine que les
  rapports HTML que vous lui demandez : aucune configuration, aucun
  cache, aucune entrée dans le système.

---

## Si quelque chose ne va pas

- **La fenêtre ne s'ouvre pas, et le terminal parle de Tkinter** : installez
  le paquet indiqué (sous Linux Mint : `sudo apt install python3-tk`).
- **Lancez `diagnose` en premier** :
  `python3 logswow-0.7.0.pyz diagnose "chemin/du/journal.txt"`. Il montre
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
  `--format pages` écrit un dossier avec une page par combat, plus
  légère à ouvrir.
