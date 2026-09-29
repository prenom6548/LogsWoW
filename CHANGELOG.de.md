# Versionsverlauf

Was jede veröffentlichte Version geändert hat, für die, die sie
benutzen. Dieser deutsche Verlauf beginnt mit 0.10.0, der ersten
Version, die Deutsch spricht; frühere Versionen sind auf Französisch in
[`CHANGELOG.md`](CHANGELOG.md) beschrieben (ab 0.9.0 auch auf Englisch
in [`CHANGELOG.en.md`](CHANGELOG.en.md)), und das technische Detail,
datiert und gemessen, steht in den datierten Abschnitten von
`CLAUDE.md`.

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
