# Versionsverlauf

Was jede veröffentlichte Version geändert hat, für die, die sie
benutzen. Dieser deutsche Verlauf beginnt mit 0.10.0, der ersten
Version, die Deutsch spricht; frühere Versionen sind auf Französisch in
[`CHANGELOG.md`](CHANGELOG.md) beschrieben (ab 0.9.0 auch auf Englisch
in [`CHANGELOG.en.md`](CHANGELOG.en.md)), und das technische Detail,
datiert und gemessen, steht in den datierten Abschnitten von
`CLAUDE.md`.

## 0.18.0 — 2026-10-02

**Eine Spezialisierung gegen eine andere, im Fenster „Verlauf“.** Ein neuer
Reiter, *Spezialisierungen*, beantwortet „wie schlägt sich diese
Spezialisierung gegenüber jener?“ mit den Durchgängen des Verlaufs. Er
bezieht sich auf einen gefolgten Charakter oder auf alle des Ordners, **jeweils
für eine Rolle**: Der Schaden eines Tanks neben dem eines Magiers ist kein
Vergleich von Spezialisierungen.

Wie bei der Entwicklung **wird nur innerhalb desselben Inhalts verglichen**:
derselbe Dungeon auf derselben Schlüsselstufe, derselbe Boss auf derselben
Schwierigkeit, und nur Durchgänge, die zählen (beendete Schlüssel, besiegte
Bosse). Die Liste links behält nur Inhalte, die mit mindestens zwei
Spezialisierungen gespielt wurden; ein Inhalt zeigt für jede Spezialisierung die
Zahl der Durchgänge, den **Median** (ein Ausreißer verfälscht ihn nicht), die
Spanne von Minimum bis Maximum, die Gegenstandsstufe und die Abweichung
gegenüber der ersten Zeile, dazu ein Balkendiagramm der Mediane (bei null
beginnend, damit ein kleiner Unterschied nicht vergrößert wird). Der Messwert
öffnet sich auf der meistgespielten Rolle (erlittener Schaden/s für Tanks,
Heilung/s, Schaden/s); erlittener Schaden wird nur Tanks zugeschrieben, für
einen Vergleich braucht es also zwei Tank-Spezialisierungen.

Es ist keine Rangliste: Die erste Zeile ist die meistgespielte, nicht die beste,
und die Abweichung hängt von Gegenstandsstufe, Spielern und Gruppe ab, was der
Reiter sagt. Eine Zeile mit weniger als drei Durchgängen ist mit ‡ markiert.
Nichts verschwindet stillschweigend: Inhalte mit nur einer Spezialisierung und
Durchgänge, deren Spezialisierung das Protokoll nicht schreibt, werden unter der
Tabelle gezählt. Die Rolle wird nun zuerst aus der Spezialisierung gelesen, was
Durchgänge korrigiert, deren Kennung beim Speichern noch unbekannt war. Keine
bestehende Zahl ändert sich.

## 0.17.0 — 2026-10-02

**Die Entwicklung eines Charakters, im Fenster „Verlauf“.** Ein neuer Reiter,
*Entwicklung*, zeigt einen der Charaktere, denen Sie folgen, Durchgang für
Durchgang. Die Ergebnisse sind **nach Inhalt** gruppiert: ein Dungeon und eine
Schlüsselstufe oder ein Boss und eine Schwierigkeit. Eine +12 wird nie mit einer
+13 verglichen, ein Kill nie mit einem Wipe: Das ließe die Zahlen etwas sagen,
was sie nicht sagen.

Für jeden Inhalt: die Zahl der Durchgänge, der erste und der letzte Wert, die
Abweichung (der letzte Durchgang gegenüber dem ersten), die Gegenstandsstufe zu
Beginn und am Ende und eine Kurve. Der Messwert öffnet sich auf dem, was für die
Rolle des Charakters zählt (**erlittener Schaden/s** für einen Tank,
**Heilung/s** für einen Heiler, **Schaden/s** für einen DPS) und wechselt mit
einem Klick; man kann auch nur Schlüssel oder nur Bosse zeigen. Eine Tabelle
listet alle Durchgänge mit ihrem Kontext: Datum, Stufe, Ergebnis (mit der
verbleibenden Gesundheit eines nicht getöteten Bosses), Dauer, Spezialisierung,
Gegenstandsstufe, Schaden/s, Heilung/s, Erlittenes/s, Tode, Zusammensetzung der
Gruppe (Tanks / Heiler / DPS) und Spielversion.

Es ist nie eine Note. Ein abgebrochener oder unterbrochener Schlüssel und ein
nicht getöteter Boss bleiben aufgelistet (mit † markiert), gehen aber nicht in
den Trend ein; der Reiter sagt, wenn ein Inhalt mehrere Spezialisierungen
mischt oder wenn Durchgänge aus einer Datei stammen, die eine ältere
LogsWoW-Version berechnet hat. Die anderen Ansichten (eine Spezialisierung
gegen eine andere, bester Schlüssel und bester Kill) folgen. Keine bestehende
Zahl ändert sich.

## 0.16.0 — 2026-10-02

**Der Verlauf: Ihre Abende aufbewahren, um sich zu vergleichen.** Eine
Schaltfläche „Verlauf…“ öffnet ein Fenster, um Abend für Abend den Verlauf Ihrer
Charaktere aufzubauen. Bei der ersten Benutzung erklärt es das Prinzip und lässt
Sie einen ersten Ordner anlegen, den Sie beliebig nennen (eine Saison, „mit meinen
Freunden“…); ein Menü erlaubt es, jederzeit weitere Ordner zu erstellen, umzubenennen
oder zu löschen und einen Abend von einem in einen anderen zu verschieben.

**Ohne Ihre Zustimmung wird nichts gespeichert.** Sie haken die Charaktere an, denen
Sie folgen: Nur sie hinterlassen ihren Namen im Verlauf; andere Spieler (zum Beispiel
eine Zufallsgruppe) erscheinen nur in den Gruppensummen. „Diesen Abend zum Verlauf
hinzufügen“ speichert ihn auf Anfrage; ein Kontrollkästchen, standardmäßig aus,
speichert jedes gelesene Protokoll, aber nur wenn ein gefolgter Charakter mitgespielt
hat. Jeder Abend ist eine kleine lesbare Datei (etwa 30 KB: die von LogsWoW berechneten
Zahlen, nie die Ereignisse des Protokolls), nur auf diesem Computer gespeichert. Einen
Abend oder einen ganzen Ordner zu löschen ist ein Klick und berührt nie Ihre
Kampfprotokolle.

Ein Schlüssel wird ganz aufbewahrt, mit jedem seiner Pulls (Dauer, Schaden, Tode und
die durchschnittliche Gesundheit der beteiligten Gegner) und seinen Bossen; ein
Raid-Boss mit seiner Schwierigkeit und, falls er nicht gefallen ist, seiner verbleibenden
Gesundheit. Raid-Trash wird nicht aufbewahrt.

Ändert sich die Spielversion zwischen zwei Protokollen (ein neuer Patch, eine neue
Erweiterung), schlägt das Fenster einen neuen Ordner vor: Das Protokoll nennt nicht die
Saison, nur die Version des Clients, und Sie entscheiden. **Die Vergleiche selbst
(Entwicklung eines Charakters, eine Spezialisierung gegen eine andere, bester Schlüssel
und bester Kill) kommen in einer späteren Version**: Diese beginnt, die Daten
aufzubewahren. Keine bestehende Zahl ändert sich.

## 0.15.1 — 2026-10-02

**Das Fenster liest sich nebeneinander, und die Ausrüstung wird
einfacher.** Die Kämpfe stehen links, rechts die Vorschau und der
Schlüsselvergleich (zwei Reiter): Sie sehen, was der Bericht sagt, ohne
die Liste zu verlassen. Der Reiter *Ausrüstung* entfällt im Fenster: Eine
Gegenstandsnummer sagt einem Spieler nichts. Die Gegenstandsstufe bleibt,
pro Spieler in der Vorschau und auf der Seite neben jedem Namen in der
Zusammensetzung der Gruppe, mit dem Durchschnitt der Gruppe. Auf der
Seite behält die Ausrüstungsansicht Platz, Gegenstand (ein Wowhead-Link)
und Stufe; die Spalten Verzauberungen und Edelsteine, die nur Nummern
zeigten, entfallen.

**Auf der Seite wird der Schlüsselvergleich zu einem Reiter** neben
„Kämpfe“, statt unten angehängt zu werden: Die Übersicht wird nicht mehr
länger. Gibt es keinen Schlüssel zu vergleichen, bleibt die Seite wie
sie war. Keine Zahl ändert sich.

## 0.15.0 — 2026-10-02

**Eine Vorschau im Fenster, bevor die Seite geschrieben wird.** Unter
der Kampfliste folgen drei Reiter dem, was Sie ankreuzen: *Übersicht*
(Dauer, Schaden, Heilung, Tode und eine Zeile pro Spieler), *Schlüssel*
(der Vergleich, siehe unten) und *Ausrüstung*. Sie sehen, was der
Bericht sagen würde, und schreiben die Seite nur, wenn Sie weitergehen
wollen.

**Zwei Schlüssel desselben Dungeons und derselben Stufe vergleichen**,
im Fenster und auf der Seite („Vergleich der Schlüssel“, unter der
Kampfliste), mit, für die Gruppe und für jeden Spieler: **Schaden pro
Sekunde**, **Heilung pro Sekunde** (Schilde eingeschlossen, wie die
Online-Seiten), Tode, und für den **Tank** der **erlittene Schaden pro
Sekunde** (was Schilde absorbiert haben, zählt mit). Die Abweichung ist
die des letzten Schlüssels gegenüber dem ersten. Verglichen werden nur
beendete Schlüssel; ein abgebrochener Schlüssel oder einer anderer Stufe
bleibt für sich.

**Die Ausrüstung der Spieler, in der Zusammenfassung jedes Kampfes.** Die
durchschnittliche Gegenstandsstufe der Gruppe und, eingeklappt unter der
Zusammensetzung, die Ausrüstung jedes Spielers: Platz, Stufe,
Verzauberungen, Edelsteine. Das Protokoll nennt Nummer und Stufe jedes
Gegenstands, nie seinen Namen, sein Symbol oder seine Werte: Diese
stammen aus der Gegenstandsdatenbank des Spiels, die LogsWoW nicht hat
(es verbindet sich mit nichts). Jeder Gegenstand ist daher eine Nummer
mit einem Wowhead-Link, dem nur bei einem Klick gefolgt wird. Der
Durchschnitt folgt der Formel des Spiels (sechzehn Plätze, ohne Hemd und
Wappenrock, eine Zweihandwaffe doppelt gezählt). Gelesen an 420 Zeilen
aus fünf Protokollen: jedes Mal achtzehn Plätze. Keine andere Zahl
ändert sich.

## 0.14.0 — 2026-09-29

**Erhaltene Nahkampfschläge, vor allem für den Tank.** Das Panel jedes
Spielers, den der Gegner mindestens zehnmal angegriffen hat, hat einen
neuen Abschnitt: wie viele Schläge trafen (davon kritisch), wie viele
vollständig absorbiert, pariert, ausgewichen, verfehlt oder geblockt
wurden, und der vermiedene Anteil. All das schreibt das Protokoll.

Er nennt auch den Anteil der Treffer, die **von hinten** kamen. Dazu
sagt das Protokoll nichts: LogsWoW leitet es aus der Position des
Angreifers und der Blickrichtung des Spielers ab, die das Protokoll
Zeile für Zeile angibt. Eine verlässliche Schätzung, keine Angabe des
Protokolls, und auf den Nahkampf beschränkt; die Seite sagt es, mit
einer Kontrolle am Kampf selbst: Das Spiel erlaubt kein Parieren oder
Ausweichen bei einem Schlag von hinten, und in den vier Schlüsseln des
Besitzers vom 29. September liegen 97 bis 98 % der Paraden und
Ausweichmanöver des Tanks tatsächlich vorn. Derselbe Tank bekam je nach
Schlüssel 24 bis 34 % seiner Treffer von hinten. Keine andere Zahl
ändert sich.

## 0.13.1 — 2026-09-29

**Der Fortschrittsbalken des Fensters ist sichtbar und nennt die
Restzeit.** Er bewegte sich durchaus, aber unter Linux zeichnete das
Design des Fensters ihn hellgrau auf grauem Grund, und er leerte sich,
sobald das Lesen fertig war: Er wirkte kaputt. Jetzt ist er blau, bleibt
voll, wenn das Lesen oder der Bericht fertig ist, und folgt der
tatsächlichen Position in der Datei statt einer Schätzung pro Zeile.
Darunter nennt die Statuszeile den Prozentsatz und die Restzeit:
„Lesen… 36 %, 401.409 Zeilen gelesen, noch etwa 30 s“. Am 364-MB-Protokoll
des Besitzers sagte die Schätzung nach vier Sekunden 45 s voraus, bei
46 s in Wirklichkeit, und lag nie mehr als 3 s daneben. Der Bericht
selbst ist in ein, zwei Sekunden geschrieben und hat keinen Countdown.

## 0.13.0 — 2026-09-29

Die vollständige Prüfung von 0.12.1, kontrolliert an Ihrem 364-MB-Log
vom 29. September.

**Korrektur: Die Pausen eines Spielers mit Begleiter waren verdeckt.**
Jeder Zauber eines Begleiters, einer Beschwörung oder eines Totems
beendete die Pause seines Besitzers: Ein Jäger, der vierzig Sekunden
lang nichts wirkte, während sein Begleiter jede Sekunde biss, zeigte null
Sekunden ohne Aktion. Nur die eigenen Zauber des Spielers zählen jetzt
für die „Zeit ohne Aktion“ und die längsten Pausen; die seiner
Beschwörungen bleiben, getrennt, bei den gewirkten Zaubern. In Ihrem Log
ändern sich 14 von 25 Spielern; der am stärksten betroffene geht in
einem Schlüssel von 283 s auf 458 s ohne Aktion.

**Korrektur: Im PvP wurde der Gegner zur Gruppe gezählt.** In einer
Arena oder auf einem Schlachtfeld schreibt das Log die Spieler der
Gegenseite als außerhalb der Gruppe und feindlich; sie wurden wie
Mitspieler behandelt: Der Gegner stand in der Rangliste, jeder
ausgetauschte Schlag zählte als Treffer eines Verbündeten, und der
verursachte Schaden blieb bei null. Sie sind jetzt Gegner, mit ihren
Begleitern, ihren Zaubern (die eine Unterbrechung abbrechen kann) und
ihren Toden. Ein Gruppenmitglied unter Gedankenkontrolle, oder das die
Gruppe kurz verlässt, bleibt in der Gruppe. Matches werden noch nicht
getrennt. In Ihrem Dungeon-Log ändert sich keine Zahl.

**Einige Wörter blieben in den englischen, deutschen und spanischen
Berichten französisch**: „et 3 autre(s)“ in der Pull-Tabelle, „autres“
in der Aufteilung nach Schule und bei den Zielen eines Heilers, „aucun“
und „absent“ am Seitenende und in `diagnose`, „Mo“ in `where`. Alles ist
übersetzt.

**Eine Dateigröße wird überall gleich geschrieben.** Das Fenster zählte
ein Megabyte als eine Million Bytes; die Seite, `diagnose` und `where`
als 1.048.576: Dasselbe Log hatte dort 364,4 MB und hier 347,5 MB. Es
ist jetzt überall eine Million Bytes, wie der Name der Einheit sagt und
wie ein Dateimanager unter Linux es anzeigt. `diagnose` schreibt seine
Zahlen auch in der Schreibweise Ihrer Sprache („1.121.188 Zeilen“).

**Weniger Speicher beim Schreiben des Berichts.** Die Seite wurde
vollständig, mehrfach, im Speicher zusammengesetzt, bevor sie
geschrieben wurde; jetzt geht sie Kampf für Kampf auf die Festplatte. In
Ihrem Log: 252 MB → 89 MB in der Spitze für die Ansicht mit Reitern,
149 MB → 88 MB für die lange Seite. Die geschriebene Seite ist bis aufs
Byte gleich.

Kleiner: `-q` hat seine Hilfezeile; die Tests laufen auch unter Python
3.14.

## 0.12.1 — 2026-09-29

**Korrektur: Die Schwelle „in der Zeit“ war von +2 bis +11 zu streng.**
Die Regel aus 0.12.0, 15 × Stufe + 185, stimmte ab +12, verlangte darunter
aber 15 bis 30 Punkte zu viel: Ein +10 in der Zeit mit 330 Punkten wäre
als „über der Zeit“ erschienen. Die Schwelle ist jetzt die Basiswertung,
die Raider.IO für jede Stufe von +2 bis +30 veröffentlicht: 125 + 15 ×
Stufe, plus 15 an jeder Affix-Stufe (+4, +7, +10 und +12), also 320 für
+10 und 335 für +11 (ab +12 ändert sich nichts). Kein Schlüssel in den
Protokollen des Besitzers ändert sein Urteil, aber ein Murder Row +10 in
19:16 mit genau 335 Punkten kam nur durch Gleichstand durch. Die Timer
der Saison, wie die API von Raider.IO sie angibt, bestätigen alle 14
Urteile dieser Protokolle.

## 0.12.0 — 2026-09-29

**Korrektur: „in der Zeit“ war falsch für einen verspätet beendeten
Schlüssel.** Ein Val Aveuglant +13, in 30:23 abgeschlossen, stand als „in
der Zeit“. Das Protokoll schreibt am Ende eines Schlüssels ein Kennzeichen,
das „abgeschlossen“ bedeutet, nicht „in der Zeit“, und es schreibt
nirgends das Zeitlimit des Dungeons. Was beides unterscheidet, ist die
Wertung, die das Spiel dem Schlüssel gibt: mindestens 15 × Stufe + 185 in
der Zeit (380 für +13), weniger bei Verspätung. Die beiden Val Aveuglant
+13 des Besitzers: 383,2 in 27:26 (in der Zeit), 319,5 in 30:23 (über der
Zeit). Von 15 abgeschlossenen Schlüsseln liegen die 14 in der Zeit alle
über der Schwelle; wirkt ein Urteil falsch, nennen Sie den Schlüssel. Ein
Schlüssel aus einem älteren Protokoll ohne Wertung ist nur
„abgeschlossen“.

**Die Pulls in der Liste links.** Jeder Schlüssel ist dort jetzt hinter
einem kleinen „+“ eingeklappt. Aufgeklappt zeigt er seine Pulls und
Bosse in der gespielten Reihenfolge („Pull 1“, „Pull 2“, der Boss,
„Pull 4“…), nummeriert wie in der Pull-Tabelle. Jeder Trash-Pull öffnet
sich wie ein Boss, mit eigenem Detail: Schaden, Heilung, Tode, Spieler,
Gegner (die Zauberreihenfolge bleibt in der Ansicht des Schlüssels, Pull
für Pull). Ein Klick auf den Namen des Schlüssels wählt ihn aus, das „+“
klappt ihn auf. Der Ordner mit Seiten hat auch eine Seite pro Pull; die
lange Seite ändert sich nicht.

Diese Ansichten kosten etwas, gemessen an einem Protokoll von 364 MB:
35 s → 45 s, 13 → 20 MB Seite, 163 → 249 MB Spitzenspeicher. Alle Zahlen
der Kämpfe sind identisch mit 0.11.0, und jeder Pull zählt genau
denselben Schaden wie seine Zeile in der Tabelle des Schlüssels (geprüft
an 143 Pulls aus fünf Protokollen).

## 0.11.0 — 2026-09-29

**Der erste Treffer, den jeder Gegner erhielt**, Pull für Pull, Bosse
eingeschlossen: für jedes Monster der Spieler, der es zuerst getroffen
hat (auch ein verfehlter Treffer zählt, er lockt das Monster genauso an),
mit welchem Zauber und zu welchem Zeitpunkt des Pulls. Der Zauber eines
Begleiters, einer Beschwörung oder eines Totems zählt für seinen
Meister. Das Protokoll schreibt es genau so: Es ist sicher. Die Liste
klappt unter jeder Zeile der Pull-Tabelle auf, und unter der Überschrift
eines einzelnen Bosskampfs.

**Wer jeden Pull eröffnet hat.** Unter jeder Zeile der Pull-Tabelle steht
die erste Handlung, die die Gruppe seit dem Ende des vorigen Pulls mit
einem Gegner verbindet: „Eröffnet von Tisane (Tank): Todesgriff, 0,4 s
vor dem ersten Treffer“. Der Zauber eines Begleiters, einer Beschwörung
oder eines Totems zählt für seinen Meister, und die Rolle des Spielers
steht neben seinem Namen. Das Protokoll hat keine Bedrohungszeile: Ein
durch Nähe angelockter Gegner (ein Body-Pull) ist nur an dem zu
erkennen, was er danach tut, und die Zeile sagt dann „Golem handelte
zuerst, gegen Braise“, als **Beta** markiert, bis Rückmeldungen
vorliegen. Da eine Heilung, Stärkung oder Bannung im Kampf den Gegner auf
den lenkt, der sie gegeben hat, fügt sie gegebenenfalls hinzu, dass
dieses Ziel gerade einem anderen Spieler geholfen hatte, und welchem: Oft
ist das der eigentliche Auslöser. Fakten, kein Urteil:
Auch ein Bodeneffekt, den das vorige Pack hinterlassen hat, kann einen
Gegner zuerst handeln lassen.

Gemessen an drei echten Dungeon-Protokollen (159 Pulls): Der Tank
eröffnet die meisten Pulls, typischerweise 0,3 bis 0,6 s vor dem ersten
Treffer; in etwa einem von sechs Pulls handelt der Gegner zuerst.

**Ein Pull endet nach 3 Sekunden ohne Schaden** statt nach 6: näher an
dem, was eine Gruppe im Spiel tut. `--pull-gap` und die Einstellung im
Fenster erlauben weiterhin einen anderen Wert. Die Summen ändern sich
nicht; nur die Einteilung in Pulls ist feiner.

## 0.10.0 — 2026-09-28

**LogsWoW spricht auch Deutsch und Spanisch.** Das Fenster, die Befehle,
`diagnose` und der Bericht gibt es jetzt in vier Sprachen. Die Wahl
bleibt automatisch (die Sprache Ihres Rechners, Englisch für eine
Sprache ohne Übersetzung); `--langue de` oder `--langue es` erzwingt
eine. Jede Sprache schreibt ihre Zahlen auf ihre Weise: „25,4 Mio.“ und
„25.361.906“ auf Deutsch, „25,4 M“ und „45,6 mil“ auf Spanisch. Die
Übersetzungen wurden sorgfältig geschrieben, aber noch nicht von
Spielern mit dieser Muttersprache gegengelesen: Ein Begriff, der falsch
klingt, kann gemeldet werden, er ist in einer Zeile korrigiert.

**Das Dezimalkomma auf Französisch.** „25,4 M“ und „180,6 Mo“ statt
„25.4 M“ und „180.6 Mo“, überall.

**Abgebrochene Schlüssel werden erkannt.** Ein neu gestarteter oder für
einen anderen verlassener Schlüssel wurde als „über der Zeit“ gezählt;
jetzt ist er „abgebrochen“. Das Spiel schreibt vor jedem neuen
Schlüssel ein leeres Ende (weder Stufe noch Zeit), das den noch offenen
schließt. Eine neue Kachel oben im Bericht, **Nicht beendete
Schlüssel**, zählt diese Schlüssel und den, den das Protokoll offen
lässt („unterbrochen“).

**Die Spalte „Neu zugeordnet“** in der Schadensrangliste, sobald ein
Kampf Unterstützungszeilen eines Rufers enthält: der Schaden jedes
Spielers, abzüglich des Anteils, den das Spiel den Stärkungen eines
Rufers gutschreibt (Ebenholzmacht, Voraussicht, Bombardements…),
zuzüglich dessen, was es ihm gutschreibt. Das ist die Neuzuordnung von
Warcraft Logs und die einzige Form von „aDPS“, die das Protokoll
erlaubt: Es schreibt nirgends, was ein Kampfrausch oder Seele der Macht
zu den Treffern der anderen beigetragen hat. Die Spalte steht neben der
Summe statt an ihrer Stelle, und die Summe der Gruppe ändert sich nicht.

**Korrektur.** Auf Englisch stand bei der Dateigröße „Mo“; richtig ist
„MB“.

Sonst ändert sich nichts: Auf fünf Protokollen (davon drei echte)
bewegt sich außer den beiden abgebrochenen Schlüsseln keine Zahl, und
die vier Sprachen liefern genau dieselben Zahlen. Die Geschwindigkeit
ist dieselbe.
