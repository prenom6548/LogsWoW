# LogsWoW

*Version française : [README.md](README.md) · English version: [README.en.md](README.en.md) · Versión en español: [README.es.md](README.es.md)*

Lesen Sie Ihre eigenen Kampfprotokolle von World of Warcraft **auf Ihrem
eigenen Rechner**: kein Konto, kein Hochladen, keine Verbindung.

Das Spiel selbst schreibt eine Datei, `WoWCombatLog.txt`, die alles
enthält, was während eines Kampfes geschehen ist. Online-Analyseseiten
lesen diese Datei, nachdem Sie sie ihnen geschickt haben. LogsWoW liest
sie dort, wo sie liegt.

Ohne weitere Angaben gestartet — ein Doppelklick auf die Datei oder
`python3 logswow-<version>.pyz` — öffnet es **ein Fenster**: Sie wählen
ein Protokoll aus der Liste der gefundenen, haken die Kämpfe an, und der
Bericht öffnet sich in Ihrem Browser. Dieselben Schritte gibt es als
Befehle, für alle, die das Terminal vorziehen:

```
python3 -m logswow report "/Pfad/zu/WoWCombatLog.txt"
```

Neben der Datei erscheint eine HTML-Seite. Sie öffnet sich offline, lädt
nichts von irgendwoher und enthält kein Skript.

Drei Darstellungen stehen zur Wahl, im Fenster oder mit `--format`:
**onglets** (Standard: eine Datei, links die Liste der Kämpfe und
Registerkarten nach Bereich), **pages** (ein Ordner, eine Seite pro
Kampf) oder **longue** (alles auf einer Seite). Die Werte der Option
bleiben französisch, wie sie es immer waren. In der Liste links ist
jeder Schlüssel hinter einem kleinen „+“ eingeklappt: Aufgeklappt zeigt
er seine Pulls und Bosse in der gespielten Reihenfolge, und jeder
Trash-Pull öffnet sich wie ein Boss, mit eigenem Detail (alles außer der
Zauberreihenfolge, die der Schlüssel schon Pull für Pull zeigt). Die
lange Seite hat sie nicht.

Das Fenster verwendet Tkinter, die grafische Bibliothek, die mit Python
geliefert wird. Unter Windows und mit dem macOS-Installer von python.org
ist sie schon vorhanden; unter Linux Mint, Ubuntu und Debian wird sie
einmalig mit `sudo apt install python3-tk` installiert (das Fenster sagt
es selbst, wenn sie fehlt). Die Befehle brauchen sie nicht.

**Deutsch, Englisch, Französisch oder Spanisch.** Das Fenster, die
Befehle und der Bericht sprechen die Sprache Ihres Rechners, wenn
LogsWoW sie kennt, sonst Englisch. `--langue de`, `en`, `fr` oder `es`
erzwingt eine davon, und die Umgebungsvariable `LOGSWOW_LANGUE` legt
eine Wahl dauerhaft fest. Die Namen von Zaubern, Bossen und Spielern
bleiben so, wie das Protokoll sie geschrieben hat, in der Sprache Ihres
Spielclients.

Die deutsche Übersetzung wurde sorgfältig erstellt, aber noch nicht von
Spielern mit Deutsch als Muttersprache gegengelesen. Ein Begriff, der
falsch klingt, kann gemeldet werden: Er ist in einer Zeile korrigiert.

## Was Sie vorher brauchen

**Die Schritt-für-Schritt-Anleitung für Windows, Linux (auch Linux Mint)
und macOS steht in [`INSTALL.de.md`](INSTALL.de.md).** Jede veröffentlichte Version
liefert eine einzige Datei, `logswow-<version>.pyz`, die so läuft, wie
sie ist: `python3 logswow-0.10.0.pyz report WoWCombatLog.txt`.

Nichts zu installieren. Python 3.8 oder neuer, sonst nichts: kein
`pip install`, keine Abhängigkeit, kein Netzwerk. Das Paket wird kopiert
oder geklont, nicht installiert; es hat absichtlich weder
`pyproject.toml` noch `setup.py`. Die Tests laufen unter Python 3.8 bis
3.14; bevorzugen Sie eine noch gepflegte Version (3.10 oder neuer im
Jahr 2026), ältere erhalten keine Sicherheitskorrekturen mehr.

Im Spiel zwei Einstellungen, einmalig:

1. **Erweiterte Kampfprotokollierung** — System → Netzwerk →
   „Erweiterte Kampfprotokollierung“. Sie bleibt von einer Sitzung zur
   nächsten aktiv. Sie fügt der Datei Positionen, Lebenspunkte und
   Ressourcen hinzu.
2. **`/combatlog`** im Chat, um die Aufzeichnung zu starten. Das bleibt
   nicht bestehen: Tippen Sie es in jeder Sitzung erneut, oder
   installieren Sie ein kleines Addon, das es beim Betreten einer Instanz
   erledigt.

Die Datei liegt unter `_retail_\Logs\`. Unter Linux liegt sie in der
Kopie von Laufwerk C, die Ihr Launcher verwaltet (Lutris, Steam mit
Proton, Bottles, Wine). Um sie zu finden:

```
python3 -m logswow where
```

## Die Befehle

| Befehl | Was er tut |
|---|---|
| *(keiner)* oder `fenetre` | öffnet das Fenster |
| `report DATEI` | schreibt die vollständige HTML-Seite |
| | `--format onglets\|pages\|longue` die Darstellung, `-o` der Dateiname (der Ordner bei `pages`), `--only` ein einzelner Kampf, `--pull-gap` wie Pulls getrennt werden, `--wowhead` die Sprache der Links, `--sans-sequence` ohne Zauberreihenfolge, `--force` um eine Datei zu überschreiben, die kein Bericht ist |
| `list DATEI` | listet die Kämpfe der Datei auf, einer pro Zeile |
| `diagnose DATEI` | zeigt, was das Programm verstanden hat und was nicht |
| `where` | sucht den `Logs`-Ordner des Spiels |
| *(alle)* | `--langue de\|en\|fr\|es\|auto` die Sprache der Oberfläche und des Berichts |

**Führen Sie `diagnose` zuerst aus**, nach jedem Patch des Spiels. Es
zeigt den Aufbau der Felder, wie er *in Ihrer Datei gemessen* wurde, die
Liste der gefundenen Ereignisse und jede Zeile, die es nicht einordnen
konnte. Ein selbstsicherer Kampfbericht aus einer falsch gelesenen Datei
wäre schlimmer als gar kein Bericht.

## Was der Bericht enthält

- **Die Kämpfe**: jeder Boss-Pull und jeder Mythisch+-Schlüssel, mit
  Dauer, Ergebnis und Anzahl der Tode. Ein Schlüssel und die Bosse darin
  erscheinen beide. Eine Begegnung, die das Spiel öffnet und schließt,
  ohne dass ein einziger Treffer landet, heißt „kein Kampf“ und zählt
  nicht als Wipe.
- **Die Zusammensetzung der Gruppe**, Tanks, Heiler und DPS, mit Klasse
  und Spezialisierung jedes Einzelnen. Sie stammen aus dem, was der
  Client zu Beginn des Kampfes schreibt; eine Spezialisierung, die das
  Werkzeug nicht kennt, wird mit ihrer Nummer angezeigt statt geraten.
- **Ein Zeitverlauf** des Schadens, den die Gruppe erlitten hat, Sekunde
  für Sekunde, mit beschrifteter Skala links und Toden in Rot. Als Kurve
  bei einem Boss-Pull das Leben des Bosses (unter dem Diagramm genannt);
  in einem Schlüssel **das gemeinsame Leben aller angegriffenen
  Gegner**, die Summe der aktuellen Lebenspunkte geteilt durch die Summe
  der Maxima, die mit jedem Pack steigt und fällt, wenn es stirbt.
- **Die Liste der Pulls**, sobald ein Kampf mehrere enthält, was bei
  jedem Mythisch+-Schlüssel der Fall ist: Beginn, Dauer, was und wie
  viel angegriffen wurde, verursachter und erlittener Schaden, Tode. Ein
  Pull mit einem Boss nennt ihn zuerst, trägt ein Abzeichen mit dem
  Ergebnis der Begegnung (Kill in Grün, Wipe in Rot) und trennt **Schaden
  auf den Boss von Schaden auf den Trash**, der mitgezogen wurde. Die
  Grenzen einer Begegnung kommen aus dem Protokoll selbst: Eine
  Begegnung, nach der keine Einheit benannt ist (ein Rat, ein Duo),
  rechnet dem Boss den gesamten Schaden während ihrer Dauer zu, und die
  Seite sagt es. Ein Pull endet nach drei Sekunden ohne Schaden in
  beide Richtungen, außer innerhalb einer Bossbegegnung, die immer ein
  einziger Pull bleibt; `--pull-gap` ändert diese Schwelle, wenn Ihre
  Gruppe Packs aneinanderreiht.
- **Wer jeden Pull eröffnet hat**, unter seiner Zeile: die erste
  Handlung, die die Gruppe seit dem Ende des vorigen Pulls mit einem
  Gegner verbindet, mit dem Spieler, seiner Rolle, dem Zauber (der einer
  Beschwörung zählt für ihren Meister) und dem Vorsprung vor dem ersten
  Treffer. Das Protokoll hat keine Bedrohungszeile: Ein durch Nähe
  angelockter Gegner ist nur an dem zu erkennen, was er danach tut, und
  die Zeile, als **Beta** markiert, sagt dann „Golem handelte zuerst,
  gegen Tisane“. Da eine Heilung, Stärkung oder Bannung im Kampf den
  Gegner auf den lenkt, der sie gegeben hat, sagt sie auch, wenn dieses
  Ziel gerade eine gegeben hatte, und wem: Das ist oft der eigentliche
  Auslöser. Fakten, kein Urteil.
- **Der erste Treffer, den jeder Gegner erhielt**, in jedem Pull, Bosse
  eingeschlossen, unter seiner Zeile aufklappbar: wer ihn zuerst
  getroffen hat (auch ein verfehlter Treffer zählt), mit welchem Zauber,
  zu welchem Zeitpunkt. Dieser ist sicher: Das Protokoll schreibt ihn
  genau so.
- **Schaden und Heilung** pro Spieler, mit DPS, HPS und dem Anteil der
  Heilung, der durch Überheilung verloren ging. **Schilde** haben eine
  eigene Spalte: Was sie absorbiert haben, ist im Protokoll keine
  Heilung, da sie Schaden verhindern, statt Leben zurückzugeben. Die
  Spalte „Summe“ addiert beides — diese Summe nennen die Online-Seiten
  „Heilung“. Der Schaden zählt, was jeder Treffer tatsächlich abgezogen
  hat: nicht den Überschuss eines Todesstoßes, wohl aber, was ein
  gegnerischer Schild geschluckt hat. Die Heilung zählt, was ein
  heilungsabsorbierender Schwächungseffekt geschluckt hat, und die
  Geistverbindung, die Leben von einem Spieler zum anderen verschiebt,
  ist weder Heilung noch erlittener Schaden.
- **Mit Warcraft Logs verglichen** auf fünf Schlüsseln, Spieler für
  Spieler: dieselben Tode für alle, derselbe Schaden auf 0,1 % genau
  (auf die Einheit genau für die Hälfte der Spieler), dieselbe Heilung
  auf die Einheit genau für 17 von 25 Spielern. Die verbleibenden
  Unterschiede haben eine bekannte Ursache, beschrieben in
  `CHANGELOG.md`.
- **Gewirkte Zauber** schließen die der Beschwörungen ein, getrennt
  gezeigt. Die Datei schreibt einen Zauber, den das Spiel selbst
  auslöst, genau wie einen von Hand gedrückten, daher ist die Anzahl
  höher als bei einer Online-Seite, die Procs anhand einer gepflegten
  Liste entfernt.
- **Schaden, den die Datei niemandem zuschreibt**, falls vorhanden: Eine
  verbündete Kreatur, deren Meister das Protokoll nie nennt, kann keinem
  Spieler zugeordnet werden. Sie bleibt außerhalb der Summe, und ein
  Kasten sagt es, mit Namen und Beträgen — eine stillschweigend zu
  kleine Summe wäre schlimmer.
- **Der Anteil eines Verstärkungs-Rufers**: Das Protokoll schreibt seinen
  Stärkungen (Ebenholzmacht, Voraussicht…) einen Teil der Treffer
  anderer Spieler gut, und ihm die Bombardements, die ein Verbündeter
  auslöst. Diese Beträge stecken bereits im Schaden derer, die die
  Treffer verursacht haben: Sie werden getrennt im Bereich des Rufers
  gezeigt, nie ein zweites Mal addiert. Warcraft Logs verschiebt sie
  dagegen zum Rufer: Die Spalte **Neu zugeordnet** in der Schadensrangliste
  macht dieselbe Verschiebung, neben der Summe statt an ihrer Stelle,
  sobald ein Kampf solche Zeilen enthält.
- **Abgebrochene Schlüssel**: Ein neu gestarteter oder für einen anderen
  verlassener Schlüssel ist „abgebrochen“, nicht „über der Zeit“, und die
  Kachel **Nicht beendete Schlüssel** zählt auch den, den das Protokoll
  offen lässt.
- **In der Zeit oder über der Zeit**: Das Protokoll sagt, dass ein
  Schlüssel abgeschlossen wurde, nie ob in der Zeit, und schreibt den
  Timer des Dungeons nicht. Das Urteil stammt aus der Wertung, die das
  Spiel am Ende des Schlüssels schreibt: Ein Schlüssel in der Zeit bringt
  mindestens die Basiswertung seiner Stufe, aus der von Raider.IO
  veröffentlichten Tabelle (125 + 15 × Stufe, plus 15 an jeder
  Affix-Stufe: +4, +7, +10 und +12; 320 für +10, 380 für +13), ein
  verspäteter weniger. Gemessen an 14 abgeschlossenen Schlüsseln: die 13
  in der Zeit 3 bis 15 Punkte darüber, der einzige verspätete 60 Punkte
  darunter, und die Timer der Saison, wie Raider.IO sie angibt,
  bestätigen jedes dieser Urteile. Ohne Wertung (älteres Format) ist der
  Schlüssel nur „abgeschlossen“.
- **Vorschau und Schlüsselvergleich im Fenster.** Rechts neben der
  Kampfliste folgen zwei Reiter dem, was Sie ankreuzen: die Übersicht
  (Dauer, Schaden, Heilung, Tode, eine Zeile pro Spieler mit seiner
  Gegenstandsstufe) und die Schlüssel. Zwei beendete Schlüssel desselben
  Dungeons und derselben Stufe werden verglichen: Schaden/s, Heilung/s
  (Schilde eingeschlossen) und, für den Tank, erlittener Schaden/s, für
  die Gruppe und für jeden Spieler. Die Seite enthält denselben
  Vergleich.
- **Die Gegenstandsstufe der Spieler**, in der Übersicht und auf der
  Seite: neben jedem Namen in der Zusammensetzung der Gruppe, mit dem
  Durchschnitt der Gruppe. Auf der Seite zeigt ein eingeklapptes Detail
  jedes Teil (Platz, Gegenstand, Stufe). Das Protokoll nennt nur Nummer
  und Stufe eines Gegenstands: Name und Symbol stammen aus der
  Gegenstandsdatenbank des Spiels, die LogsWoW nicht hat; jeder
  Gegenstand ist daher eine Nummer mit einem Wowhead-Link, dem nur bei
  einem Klick gefolgt wird.
- **Erhaltene Nahkampfschläge**, im Panel jedes Spielers, den der
  Gegner mindestens zehnmal angegriffen hat (vor allem der Tank):
  getroffen, kritisch, vollständig absorbiert, pariert, ausgewichen,
  verfehlt, geblockt, so wie das Protokoll sie schreibt. Dazu der Anteil
  der Treffer, die **von hinten** kamen: Das Protokoll schreibt es nicht,
  LogsWoW leitet es aus der Position des Angreifers und der
  Blickrichtung des Spielers ab. Eine verlässliche Schätzung, keine
  Angabe des Protokolls, und auf den Nahkampf beschränkt; die Seite sagt
  es, mit einer Kontrolle: Das Spiel erlaubt kein Parieren oder
  Ausweichen von hinten, und 97 bis 98 % der Paraden und
  Ausweichmanöver liegen in den gemessenen Schlüsseln tatsächlich vorn.
- **Physisch oder magisch**: der Anteil des erlittenen und verursachten
  Schadens, der physisch, magisch oder beides war, in Prozent, über den
  ganzen Kampf und dann Pull für Pull, mit dem Detail nach Schule
  (Schatten, Feuer, Natur…).
- **Was der Gruppe geschadet hat**: jede gegnerische Fähigkeit, wie viel
  sie gekostet hat, wie viele Spieler sie getroffen hat.
- **Die Tode**, jeder mit der Kette der letzten erhaltenen Treffer und
  Heilungen vor dem Ende und dem verbleibenden Leben bei jedem Schritt.
- **Was die Gruppe verhindert hat**: wie viele Zauber der Gegner begonnen
  hat, wie viele abgeschlossen wurden, wie viele durch eine Unterbrechung
  abgebrochen wurden und wie viele endeten, weil der Wirker starb.
- **Pro Spieler**, durch Aufklappen seines Namens: für jeden Zauber die
  Summe, der Anteil, die Anzahl der Wirkungen und Treffer, der
  Durchschnitt, die Kritrate, der Wert pro Sekunde und das Hauptziel.
  Dann seine Heilung mit Überheilung und wem sie zugutekam, was er
  abbekommen hat und von wem, die erhaltenen Stärkungen **mit dem, der
  sie gegeben hat**, die erlittenen Schwächungen, was er selbst
  angewendet hat und auf wen, seine Unterbrechungen und Bannungen mit dem
  Namen dessen, was abgebrochen wurde, und seine längsten Pausen ohne
  Zauber.
- **Die Zauberreihenfolge, Pull für Pull**, unten im Bereich jedes
  Spielers: jeder gewirkte Zauber, der Reihe nach, als Marke in fester
  Farbe mit seinen ersten beiden Buchstaben. Beim Überfahren erscheinen
  Name und Zeitpunkt, ein Klick öffnet Wowhead. Die Legende ist ein
  Filter: Ein Klick auf einen Zauber blendet alle seine Marken aus oder
  ein, ohne Skript in der Seite. Die Zauber seiner Beschwörungen stehen
  getrennt, als runde Marken. Was das Spiel von selbst auslöst, steht im
  Protokoll genau wie ein Tastendruck; Zauber mit den typischen Merkmalen
  (nie bezahlt und zusammen mit einem bezahlten Zauber gewirkt, oder
  schneller als jede Taste, oder die zweite Kopie eines Zaubers, den das
  Protokoll zweimal unter demselben Namen schreibt) werden getrennt
  gruppiert und zunächst ausgeblendet; ein Klick zeigt sie.
  `--sans-sequence` lässt den Bereich weg, für eine etwa halb so große
  Seite.
- **Pro Gegner** auf dieselbe Weise: Einheiten mit gleichem Namen werden
  gruppiert, mit dem, was sie verursacht haben und bei wem, was sie
  erlitten haben und von wem, den gewirkten Zaubern und wie viele getötet
  wurden.
- **PvP, teilweise**: In einer Arena oder auf einem Schlachtfeld sind die
  Spieler der Gegenseite (außerhalb der Gruppe und feindlich, so wie das
  Log sie schreibt) Gegner, nie die Gruppe; ein Gruppenmitglied unter
  Gedankenkontrolle bleibt in der Gruppe. Matches werden noch nicht
  getrennt: Ohne Begegnung und ohne Schlüssel in der Datei ist das ganze
  Log eine einzige „Sitzung“.
- **Zaubernamen sind Links zu Wowhead**, in der Sprache Ihres Rechners.
  `--wowhead de` erzwingt eine Sprache, `--wowhead off` entfernt die
  Links. Beim Öffnen der Seite wird nichts geladen: Ein Link wird nur
  verfolgt, wenn Sie ihn anklicken.

Ein ganzer Abend ergibt eine Seite von mehreren Megabyte. Um nur einen
Teil davon anzusehen:

```
python3 -m logswow list WoWCombatLog.txt          # die Kämpfe ansehen
python3 -m logswow report WoWCombatLog.txt --only 5
python3 -m logswow report WoWCombatLog.txt --only "Nalorakk"
```

## Was es nicht tut, und warum

- **Es vergleicht Sie mit niemandem.** Ein Perzentil braucht die
  Protokolle aller anderen Spieler. Genau das hat ein lokales Werkzeug
  auf Ihrem Rechner nicht, und es ist der einzige echte Dienst, den eine
  zentrale Seite leistet.
- **Es sagt nicht, ob ein Treffer vermeidbar war.** Die Datei sagt, wer
  getroffen wurde und wie stark; zu wissen, dass ein Schaden von einem
  Bodeneffekt kam, setzt voraus, den Boss zu kennen. Dieses Werkzeug
  behauptet das nicht.
- **Es weiß nicht, was ein Kontrolleffekt ist.** Das Protokoll schreibt
  nirgends, dass ein Zauber eine Betäubung oder eine Furcht ist. Ein
  gegnerischer Zauber, der ohne Unterbrechung und ohne Tod des Wirkers
  endet, steht daher unter „Ursache nicht im Protokoll“. Einen
  Kontrolleffekt von einer gewöhnlichen Schwächung zu unterscheiden,
  bräuchte eine gepflegte Zauberliste.
- **Es berechnet keinen Prozentsatz der Schadensminderung.** Das
  Protokoll schreibt nirgends, was ein Treffer *vor* Rüstung und
  Schadensverringerungen bewirkt hätte. Die zweite Zahl jedes Treffers
  sieht danach aus und ist es nicht: Auf einem echten Schlüssel gemessen
  ist sie bei einem normalen Treffer das 1,03-Fache des erlittenen
  Schadens und bei einem kritischen das 2,59-Fache — es ist der Betrag
  vor dem kritischen Multiplikator. Das eine durch das andere zu teilen,
  ergibt einen glaubwürdigen, falschen Prozentsatz. Was wirklich in der
  Datei steht und gezeigt wird, ist der **von Schilden absorbierte
  Schaden**.
- **Es berechnet kein aDPS im Sinne von FF Logs.** FF Logs liest den
  Anteil einer Stärkung nicht aus dem Protokoll: Es berechnet ihn, aus
  einer gepflegten Tabelle des Multiplikators jeder Stärkung und, bei
  einer Stärkung der kritischen Trefferchance, aus der Wahrscheinlichkeit,
  dass der kritische Treffer von ihr kam. Das Protokoll von WoW schreibt
  diesen Anteil selbst nur für die Stärkungen eines Rufers, und genau das
  zeigt die Spalte **Neu zugeordnet**: die Formel des rDPS (Schaden −
  Anteil aus fremden Stärkungen + an andere gegebener Anteil), auf diese
  Stärkungen beschränkt. Für die übrigen bräuchte es dieselbe gepflegte
  Tabelle; und eine Tempo-Stärkung (Kampfrausch, Seele der Macht) ändert
  die Zahl der Treffer, was keine dieser Formeln behandelt.
- **Es beurteilt Ihre Rotation nicht.** Es zeigt Ihre Pausen, Ihre
  Fähigkeiten und Ihre aktiven Effekte. „Hier hätten Sie das drücken
  sollen“ zu sagen, braucht die Regeln Ihrer Spezialisierung,
  geschrieben und gepflegt von jemandem, der sie spielt.

Diese Grenzen sind strukturell, keine fehlenden Funktionen.

## Wo Ihre Daten sind

Auf Ihrer Festplatte und nirgendwo sonst. Das Programm öffnet eine
Datei, schreibt eine Datei und beendet sich. Es öffnet keine
Netzwerkverbindung, liest keine Konfiguration, schreibt keinen
Zwischenspeicher und kennt kein Konto. Die erzeugte Seite lädt beim
Öffnen nichts: Der Test `test_writes_a_self_contained_page` schlägt
fehl, wenn sich ein `<script>`, ein Stylesheet, ein `src=`, ein
`@import` oder ein `url(` einschleicht, und wenn eine andere Adresse als
Wowhead darin vorkommt. Wowhead-Links werden nur verfolgt, wenn Sie sie
anklicken.

Der Bericht schreibt nie den **Realm** eines Spielers: Namen erscheinen
in ihrer Kurzform, in den Tabellen wie in den Todesketten. Ein
Bildschirmfoto des Berichts identifiziert daher weniger als eines des
Protokolls.

Eine nützliche Erinnerung: Ein Kampfprotokoll enthält die Namen und
Leistungen **der ganzen Gruppe**, nicht nur Ihre. **Der HTML-Bericht
ebenso**: ohne Realms, aber mit dem Kurznamen, dem Schaden, der Heilung
und den Toden jedes Einzelnen. Teilen Sie ihn nur mit dem Einverständnis
der Genannten, wie das Protokoll selbst.

`report` weigert sich, eine vorhandene Datei zu überschreiben, die kein
LogsWoW-Bericht ist (etwa ein anderes Protokoll), außer mit `--force`,
und überschreibt nie das gelesene Protokoll, auch nicht mit `--force`.

## Tests und Prüfung an einem echten Protokoll

```
python3 tests/run-tests.py
python3 tools/check-invariants.py WoWCombatLog.txt
ln -s ../../tools/pre-push .git/hooks/pre-push     # einmalig, für Mitwirkende
```

Die Tests laufen ohne Abhängigkeit und ohne Netzwerk auf
`examples/exemple-combat.txt`, einem für dieses Repository **erfundenen**
Protokoll: Kein echtes Protokoll wird je eingecheckt, gerade wegen der
Erinnerung oben. Die Tests lesen Französisch, unabhängig von der Sprache
des Rechners; die Tests der anderen Sprachen fordern ihre Sprache an.

Das zweite Skript nimmt ein **echtes** Protokoll und prüft, ob die
Rechnungen zusammenpassen: Der Schaden der Gruppe ist die Summe
desjenigen der Spieler, der eines Spielers die Summe seiner Zauber, der
eines Zaubers die Summe über seine Ziele; dasselbe für die Heilung; auf
drei Arten gezählte Tode ergeben dieselbe Zahl; keine Effektdauer
überschreitet den Kampf; begonnene gegnerische Zauber sind gleich der
Summe ihrer Ergebnisse; der Anteil, den das Spiel einem Rufer
gutschreibt, ist gleich dem, der den Spielern abgezogen wird. Es fand
beim ersten Lauf einen Fehler. Es sagt nicht, ob eine Zahl stimmt, nur
ob die Zahlen zueinander passen. Es prüft die ganze Datei auch nach
einem ersten Fehler und zieht am Ende Bilanz.

Bei einem Push läuft nichts online: Der Hook `tools/pre-push` wiederholt
diese Prüfungen vor jedem Push auf Ihrem Rechner. Nur das
**Veröffentlichen einer Version** läuft über eine GitHub-Aktion
(`.github/workflows/release.yml`), gestartet entweder über die
Schaltfläche „Run workflow“ im Reiter Actions (auf `main`) oder über ein
aus einer Kopie des Repositorys gepushtes Tag wie `v0.2.0`: Sie führt
die Tests erneut aus, prüft, dass das Tag die Version des Pakets ist und
auf `main` liegt, baut die `.pyz` und ihren Fingerabdruck `SHA256SUMS`
und veröffentlicht sie mit den Hinweisen zur Version. Sie verwendet nur,
was der Rechner von GitHub schon hat, ohne Aktion von Dritten.

Was sich von einer Version zur nächsten ändert, steht in
[`CHANGELOG.de.md`](CHANGELOG.de.md) (ab 0.10.0; frühere Versionen auf
Französisch in [`CHANGELOG.md`](CHANGELOG.md) und ab 0.9.0 auf Englisch
in [`CHANGELOG.en.md`](CHANGELOG.en.md)); das technische Detail, datiert
und gemessen, in den datierten Abschnitten von `CLAUDE.md`.

Das Protokoll wird so gelesen, wie das Spiel es schreibt, mit seinen
Windows-Zeilenenden, unter Linux wie unter Windows.

## Lizenz

GNU Affero General Public License, **Version 3 oder (nach Ihrer Wahl)
jede spätere Version** (AGPL-3.0-or-later), seit Version 0.8.0. Jeder
darf das Programm nutzen, ändern und weitergeben; wer eine Version
verbreitet, geändert oder nicht, muss ihren Quellcode unter derselben
Lizenz bereitstellen. Die AGPL fügt der GPL einen Punkt hinzu: **Wer
eine geänderte Version als Online-Dienst betreibt** (etwa eine Seite,
die Ihre Protokolle liest), muss den Nutzern ebenfalls ihren Quellcode
anbieten. Für Sie, bei der Nutzung auf Ihrem Rechner, ändert sich
nichts. Seit dem 28. September 2026 werden auch die früheren Versionen
(0.1.0 bis 0.7.0) unter AGPL-3.0-or-later verbreitet; wer bereits eine
Kopie besaß, behält für diese Kopie die Rechte der GPL, unter der er sie
erhalten hat, die die GPL für unwiderruflich erklärt. Siehe `LICENSE`
und `PROVENANCE.md`.

Maßgeblich ist der englische Wortlaut der Lizenz in `LICENSE`; diese
Zusammenfassung dient nur der Orientierung.
