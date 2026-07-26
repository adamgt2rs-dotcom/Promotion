# Analyse-Briefing: Signalbasierte Werkzeugverschleißschätzung beim Bohren von DA718

> Diese Datei ist als Startkontext für eine neue Claude Code Session gedacht. Am besten direkt als `CLAUDE.md` im Projektordner ablegen (Claude Code liest diese Datei automatisch als Projektkontext) oder zu Beginn des Chats einfügen.

## 1. Projektkontext

- Promotionsprojekt **T26137 RECAP** (MTU Aero Engines / TU München): Probabilistische Zuverlässigkeitsabsicherung des Bohrprozesses hochbelasteter Turbinenscheiben aus DA718.
- Diese Analyse adressiert **Forschungsfrage 1**: Wie können interne Maschinensignale genutzt werden, um Werkzeugverschleiß beim Bohren zuverlässig zu schätzen?
- Ziel: methodische Vorarbeit für einen ersten Konferenzbeitrag (VDI-Fachtagung Technische Zuverlässigkeit 2027, Kurzfassung fällig 14.09.2026, Schwerpunkt "Prognostics and Health Management (PHM)").
- Arbeitstitel des Beitrags: *Signalbasierte Schätzung des geeignetsten Werkzeugverschleißes beim Bohren von [Nickelbasis-Turbinenscheiben]* (Materialbezeichnung im finalen Titel noch zu prüfen, siehe Hinweis "ohne Produkt-/Firmennamen" im Call for Papers).
- Die eigentlichen Promotions-Versuchsdaten (Original-Prozess, 8,6 mm Fräser mit vier Schneiden als Ausbohrer) liegen erst ab **November 2026** vor. Die hier zu analysierenden Daten stammen aus der **Masterarbeit** des Autors (kleinerer Pilotprozess) und werden als methodische Vorstudie für den Konferenzbeitrag verwendet.

## 2. Datenherkunft

- Ursprünglicher Zweck der Masterarbeit: *"Methode zur Beurteilung von Prozessüberwachungssystemen für die Herstellung von Bohrungen in Flugantrieben mittels statistischer Gütekennzahlen"* — die Daten wurden also ursprünglich zur Bewertung von Überwachungssystemen erhoben, nicht zur Verschleißschätzung. Sie werden hier zweckneu für die Verschleißschätzung ausgewertet.
- Bohrprozess (Masterarbeit/Pilotstudie): zweistufiger Prozess mit einem **6,3 mm, sechsschneidigen, stirnschneidenden Ausbohrwerkzeug** (kleinerer Durchmesser als in der Promotion, dort 8,6 mm / 4 Schneiden).
- Werkstoffe: **DA718** (primär) und **IN718** (Vergleichsdatensatz, geringere Streuung als DA718 — als Sekundäranalyse/Diskussionspunkt, nicht in die Hauptmodellierung mischen).
- Signalquellen: **interne Maschinensignale** (Spindel- und Antriebsströme) als Hauptquelle; zusätzlich **externe Kraft-/Drehmomentmessung** als Referenz, die die Validität der internen Signale bereits bestätigt hat.
- Verschleißmessung: Freiflächenverschleiß (VB, Mittelwert) und VBmax, gemessen per Digitalmikroskop nach definierten Bohrungsintervallen.

## 3. Datenstruktur (DA718-Datensatz)

- **3 Turbinenscheiben** aus DA718, gleicher Lochkreis (gleiche Lochpositionen je Scheibe).
- Scheibe 1: 40 Verschleißmesspunkte = 8 Werkzeuge × 5 Messpunkte
- Scheibe 2: 40 Verschleißmesspunkte = 8 Werkzeuge × 5 Messpunkte
- Scheibe 3: 36 Verschleißmesspunkte (Werkzeug-/Messpunktaufteilung ggf. abweichend — beim Datenimport prüfen und dokumentieren, z. B. falls ein Werkzeug vorzeitig ausgeschieden ist)
- Messpunkte jeweils bei den **Bohrungen Nr. 2, 6, 10, 14 und 18** pro Werkzeug.
- Zu jedem Messpunkt liegen die zugehörigen **Signalkennzahlen** vor: Maximalwert, Mittelwert, Standardabweichung (je Signalkanal — genaue Kanalzahl/-namen beim Import klären, z. B. Spindelstrom, Vorschubachsenstrom o. ä.).
- **Wichtig:** Prozesssignale liegen für **alle** Bohrungen vor, nicht nur für die 5 Messpunkte je Werkzeug — das ermöglicht später die Rekonstruktion einer vollständigen Verschleißkurve (siehe Schritt 5 unten), auch für Bohrungen ohne direkte Verschleißmessung.

### Empfohlenes Datei-/Tabellenschema (Long-Format)

Falls die Rohdaten noch nicht in dieser Form vorliegen, bitte vor dem Import so aufbereiten (eine Zeile je Messpunkt):

```
scheibe_id, werkzeug_id, bohrung_nr, VB, VBmax, sig1_max, sig1_mean, sig1_std, sig2_max, sig2_mean, sig2_std, ...
```

Zusätzlich eine zweite Tabelle für die **durchgehenden Signaldaten aller Bohrungen** (auch der nicht vermessenen), gleiche Struktur ohne VB/VBmax:

```
scheibe_id, werkzeug_id, bohrung_nr, sig1_max, sig1_mean, sig1_std, sig2_max, sig2_mean, sig2_std, ...
```

Der IN718-Datensatz separat in gleicher Struktur, mit einer zusätzlichen Spalte `werkstoff` (DA718/IN718), falls beide Tabellen später zusammengeführt werden sollen.

## 4. Zielsetzung der Analyse

Schätzung von Werkzeugverschleiß (VB und/oder VBmax) aus Signalkennzahlen, mit zwei konkreten Fragestellungen:

1. **Welche Verschleißkenngröße (VB oder VBmax) lässt sich robuster aus den Signalen schätzen?** (→ Kernaussage für die Kurzfassung: "geeignetster Werkzeugverschleiß")
2. **Wie gut generalisiert das Modell auf neue, ungesehene Werkzeuge/Scheiben?**

## 5. Empfohlene Vorgehensweise (Pipeline)

Bitte in dieser Reihenfolge vorgehen, nicht alle Modelle parallel:

1. **Explorative Datenanalyse zuerst.** Verteilungen von VB/VBmax, Streudiagramme Signalkennzahl vs. Verschleiß, Verschleißverlauf pro Werkzeug (VB über Bohrungsnummer 2→6→10→14→18), Vergleich der drei Scheiben. Auffälligkeiten (z. B. das abweichende Scheibe-3-Muster) dokumentieren.

2. **Baseline: einfache lineare Regression.** Eine Signalkennzahl → VB (und separat → VBmax). Je Signalkennzahl einzeln testen, um zu sehen, welche allein am meisten erklärt.

3. **Multiple lineare Regression.** Mehrere Signalkennzahlen kombiniert → VB/VBmax. Auf Multikollinearität zwischen den Kennzahlen achten (z. B. Max/Mittelwert/Std desselben Signals können stark korreliert sein).

4. **Validierungsprotokoll — zwingend gruppenbasiert, kein zufälliger Split:**
   Die Daten sind hierarchisch verschachtelt (Messpunkte innerhalb Werkzeug innerhalb Scheibe) — mehrere Messpunkte desselben Werkzeugs sind stark korreliert. Ein zufälliger Train/Test-Split würde das Ergebnis durch Data Leakage optimistisch verzerren.
   - **Leave-one-tool-out** Kreuzvalidierung als Hauptprotokoll (ein Werkzeug jeweils als Testset, Rest als Training).
   - Zusätzlich **leave-one-disk-out** (auf 2 Scheiben trainieren, auf der dritten testen) als strengerer Test der Generalisierung über Scheiben hinweg.
   - Metriken je Fold: RMSE, MAE, R² (ggf. MAPE, falls sinnvoll skaliert).

5. **Danach erst klassische ML-Modelle vergleichen:** Random Forest, Gradient Boosting — mit demselben Validierungsprotokoll wie Schritt 4, damit die Ergebnisse fair vergleichbar sind. Da die Stichprobe klein ist (~116 Messpunkte gesamt), auf Overfitting achten (z. B. Lernkurven, einfache Hyperparameter, Regularisierung). Nur weitergehen, wenn die Daten tatsächlich einen Mehrwert gegenüber der Regression zeigen — sonst ehrlich dokumentieren, dass die Regression bereits ausreicht.

6. **Anwendung auf alle Bohrungen (nicht nur Messpunkte):** Mit dem validierten Modell aus Schritt 4/5 den Verschleiß für *alle* Bohrungen schätzen (nicht nur die 5 gemessenen), da Signaldaten durchgehend vorliegen. Ergebnis: rekonstruierte, geschätzte Verschleißkurve pro Werkzeug — das ist die anschaulichste Abbildung für die Publikation.

7. **Optional/sekundär:** Gleiche Pipeline auf IN718-Daten anwenden und Ergebnis gegenüberstellen (Diskussionspunkt: bestätigt die höhere DA718-Streuung als werkstoffbedingt, nicht methodisch bedingt).

## 6. Methodische Leitplanken (bitte konsequent einhalten)

- **Kein zufälliger Train/Test-Split** — immer gruppenbasiert nach Werkzeug bzw. Scheibe (siehe Schritt 4).
- **Kleine Stichprobe im Blick behalten** (~40/40/36 Punkte je Scheibe) — Konfidenzintervalle bzw. Streuung der CV-Metriken über die Folds mit angeben, nicht nur Mittelwerte.
- **Feature-Skalierung** (z. B. StandardScaler) vor Regression/ML, insbesondere wenn Signalkennzahlen unterschiedliche Größenordnungen haben.
- **Multikollinearität** zwischen Max/Mittelwert/Std desselben Signalkanals prüfen (z. B. Korrelationsmatrix, VIF) vor der multiplen Regression.
- **Transparenz vor Komplexität:** Wenn Random Forest/Gradient Boosting keinen klaren Mehrwert gegenüber der (multiplen) linearen Regression zeigen, ist das ein valides und berichtenswertes Ergebnis — nicht zwingend das komplexere Modell "gewinnen lassen".
- Ergebnisse so aufbereiten, dass sie später mit Unsicherheitsangaben (Konfidenz-/Vorhersageintervalle) kompatibel sind — das ist die methodische Brücke zum eigentlichen Promotionskern (Bayes/GP), auch wenn diese Vorstudie nur Regression/klassisches ML nutzt.

## 7. Erwartete Ergebnisse (Deliverables dieser Analyse)

1. Vergleichstabelle aller Modelle (einfache Regression je Kennzahl, multiple Regression, Random Forest, Gradient Boosting) mit CV-Metriken (RMSE/MAE/R², Mittelwert ± Streuung über Folds), getrennt für VB und VBmax.
2. Klare Aussage, welche Verschleißkenngröße (VB oder VBmax) robuster schätzbar ist.
3. Mindestens eine Abbildung: rekonstruierte Verschleißkurve (geschätzt vs. gemessen) für ein Beispielwerkzeug.
4. Kurze schriftliche Zusammenfassung (5–10 Sätze) der Kernergebnisse — als Grundlage für die Kernaussagen und die Innovationsgrad-Aussage der VDI-Kurzfassung.
5. Optional: DA718-vs-IN718-Vergleich als Diskussionsabschnitt.

## 8. Erste Schritte für Claude Code

1. Projektstruktur anlegen (z. B. `data/`, `notebooks_oder_scripts/`, `results/`).
2. Nutzer nach den Rohdatendateien fragen bzw. beim Import-Skript helfen, falls die Daten noch nicht im empfohlenen Schema (Abschnitt 3) vorliegen.
3. Explorative Datenanalyse (Schritt 1) durchführen und Zwischenstand mit dem Nutzer abstimmen, bevor die Modellierung beginnt.
4. Pipeline aus Abschnitt 5 schrittweise umsetzen, nach jedem Schritt kurz Zwischenergebnisse zeigen statt alles auf einmal durchzurechnen.
