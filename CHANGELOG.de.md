# Versionsverlauf

Was jede veröffentlichte Version geändert hat, für die, die sie
benutzen. Dieser deutsche Verlauf beginnt mit 0.10.0, der ersten
Version, die Deutsch spricht; frühere Versionen sind auf Französisch in
[`CHANGELOG.md`](CHANGELOG.md) beschrieben (ab 0.9.0 auch auf Englisch
in [`CHANGELOG.en.md`](CHANGELOG.en.md)), und das technische Detail,
datiert und gemessen, steht in den datierten Abschnitten von
`CLAUDE.md`.

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
