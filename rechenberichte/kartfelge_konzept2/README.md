# Rechenbericht Kompakte Kartfelge, Konzept 2 (Mathcad Prime 12)

`Rechenbericht_Kartfelge_Konzept2_Lenhard.mcdx` ist der Rechenbericht „Kompakte Kartfelge, Konzept 2
(neue Felge, Bestandsnabe)“ vom 11.11.2026 als rechnendes Mathcad-Prime-Arbeitsblatt. Aufbau wie im
Rechenbericht Pneumatik-Spanner: Deckblatt, Inhaltsverzeichnis, je Abschnitt zentrierte Überschrift,
nummerierte Teilschritte, `:=`-Definitionen mit Einheiten, Ergebnisse mit `=`, Nachweise mit Bewertung.
Kopfzeile „Lenhard“, Fußzeile mit Datum und „Seite x von y“, A4, 19 Seiten.

Die Datei ist für **Mathcad Prime 12** gestempelt (Versionsstempel und Einstellungen aus einem
Prime-12.0.0.1-Arbeitsblatt). Ältere Prime-Versionen öffnen sie nicht. Mathcad rechnet beim Öffnen alles
selbst nach; die Datei enthält keine gespeicherten Ergebnisse.

## Stand 2: Anpassung für Prime 12

Die erste Fassung ließ sich in Prime 11 und 12 nicht öffnen. Daraufhin wurde jedes Element, jedes Attribut,
jeder Attributwert und jede Formelstruktur mit 89 von Prime 11/12 gespeicherten Arbeitsblättern abgeglichen
(`generator/unseen*.py`). Alles, was Prime selbst nie so schreibt, ist ersetzt:

- `TextAlignment` an Textabsätzen (in allen Textbereichen) und zentrierte/rechtsbündige Ausrichtung:
  Text ist jetzt immer linksbündig wie bei Prime; Zentrieren erfolgt über die Position des Bereichs.
- Sprachkennung der Textbereiche `de-de` → `en-us` (wie in allen Prime-Dateien).
- Alleinstehende Vergleiche (z. B. `S_D ≥ 1,5`) → ausgewertete Bewertung `Nachweis(S_D, 1.5) = "erfüllt"`.
- `(20 mm)³` → eigene Größe `d_20`; negatives Funktionsargument → eigene Größe `F_y3`.
- Titel in den Dokumenteigenschaften entfernt; Bildgrößen ganzzahlig; ZIP wie von Prime gepackt.
- Versionsstempel Prime 11.0.1 → Prime 12.0.0.1.

## Stand 3: Seitenzahl-Vorlage

Prime 12 meldete beim Öffnen „Der Dateityp wird nicht unterstützt“ mit der Schemameldung
`The Template attribute is invalid - The value 'Seite_@PageNo_von_@PagesTotal' is invalid according to its
datatype`. Prime prüft die Datei beim Laden gegen sein Schema; die Seitenzahl darf nur eine von acht festen
Vorlagen sein (Aufzählung `pageNumberTemplate` in Prime 12.0.1.0, z. B. `@PageNo`, `Page_@PageNo`,
`@PageNo_of_@PagesTotal`, `Page_@PageNo_of_@PagesTotal`). Verwendet wird jetzt
`Page_@PageNo_of_@PagesTotal`; die deutsche Oberfläche zeigt das als „Seite x von y“ an.

Außerdem sind die letzten drei ungewohnten Formel-Kombinationen ersetzt (Vergleiche in `if` nur noch mit
`<` und `≥`, negative Größe `F_y3` als reine Definition). Der Abgleich mit den echten Prime-Dateien findet
jetzt keine einzige Abweichung mehr: kein Element, kein Attribut, kein Attributwert und keine
Formelstruktur, die Prime nicht selbst schreibt.

### Falls die Datei trotzdem nicht öffnet

Im Ordner `Diagnose/` liegen drei kleine Teildateien aus demselben Generator:
`Test_A_nur_Formeln.mcdx`, `Test_B_nur_Text.mcdx` (mit Kopf-/Fußzeile) und `Test_C_nur_Bilder.mcdx`.
Welche davon sich öffnen lässt, und die genaue Fehlermeldung von Prime, zeigen den verursachenden Teil.

## Prüfung

- Jede Formel wurde beim Erzeugen mit Einheiten nachgerechnet, in der Reihenfolge, in der Prime auswertet
  (oben nach unten, links nach rechts). Es gibt keine undefinierten Variablen, keine Einheitenfehler und keine
  doppelten Definitionen. Alle Werte stehen in `Pruefprotokoll.txt`.
- Die Plattenbeiwerte der Radscheibe (β = 0,569 eingespannt, 0,855 gelenkig, Axiallast 0,226 / 0,437) und
  der Kippwinkel wurden unabhängig mit der Kirchhoff-Plattentheorie nachgerechnet (`generator/plate_check.py`).
- `worksheet.xml`, Kopf- und Fußzeile, alle Formeln, `result.xml` und `presentation.xml` sind gegen die
  XSD-Schemata worksheet50, math50, result10 und presentation10 gültig; Relationships und XAML-Pakete sind
  konsistent (`generator/validate.py`). Die Schemata prüfen Bilder, Seitenumbrüche und Kopf-/Fußzeilen nur
  locker; dafür gibt es den Abgleich mit echten Prime-Dateien.
- Nicht geprüft: das Öffnen in Mathcad Prime selbst (hier kein Windows/Prime verfügbar).

## Abweichungen gegenüber dem PDF-Bericht

| Stelle | PDF | Mathcad-Datei | Grund |
|---|---|---|---|
| Schub im Achsschenkel | 11 N/mm² | 6,9 N/mm² | größte Querkraft ist \|F_A2\| = 1181 N (zwischen den Lagern), nicht F_B |
| Klaffsicherheit Radbolzen | 3,1 (F_V/F_B) | 3,92 = F_V/((1−Φ)·F_B) | passend zur Restklemmkraft; zusätzlich Nachweis mit Anziehfaktor 1,6 |
| Dauerhaltbarkeit Radbolzen | ±50 N/mm², S = 4,6 | σ_ASV = 54,2 N/mm² (VDI 2230), S = 4,97 | Formel statt Schätzwert |
| Lebensdauer Lager B | 89 000 km | 89 233 km | Rundung |

Alle übrigen Werte stimmen mit dem PDF überein (z. B. F_A = 1181 N, F_B = 1915 N, P_B = 2247 N,
S_0B = 1,70, σ_b = 223 N/mm², S_D = 1,71, M_K = 173,5 N·m, σ_Scheibe = 12,4 / 18,6 N/mm²).

## Neu erzeugen

```
python generator/figures.py generator/img
python generator/build_kartfelge.py <ziel.mcdx> <beliebiges Prime-12-Arbeitsblatt.mcdx> generator/img
python generator/validate.py <ziel.mcdx> <Ordner mit worksheet50.xsd usw.>
python generator/unseen.py <ziel.mcdx> <Ordner mit Prime-Arbeitsblättern>
```

Das Prime-12-Arbeitsblatt liefert nur Versionsstempel und Standard-Einstellungen. Benötigt: Python 3.10+,
matplotlib (Skizzen), sympy/numpy (nur `plate_check.py`), lxml (Prüfskripte).

## Kurzfassung: Kräfte, Wellendurchmesser, Lager (19.11.2026)

`Rechenbericht_Kartfelge_Lenhard.mcdx` ist die gekürzte Fassung im Stil des Rechenberichts Pneumatik-Spanner:
Deckblatt, Inhaltsverzeichnis, dann Kräfteberechnung (Seite 3–5), Wellenberechnung Achsschenkel Ø17
(Seite 6–8) und Lagerberechnung 6003 (Seite 9–11). Eingabewerte stehen rechts, jede Formel mit `:=` und
darunter das Ergebnis mit `=`, Nachweise als Vergleich (z. B. `σb < σbzul`), ohne Erläuterungstexte.
Erzeugt mit `generator/build_bericht2.py`; alle Ergebnisse in `Pruefprotokoll_Kraefte_Welle_Lager.txt`.

Vorzeichen der Lagerkräfte wie im Freikörperbild: F_A nach oben, F_B nach unten positiv
(Kurve außen: F_A = 1181 N, F_B = 1915 N; negative Werte wirken entgegengesetzt).

### Prime 11.0.0.0 (19.11.2026)

`Rechenbericht_Kartfelge_Lenhard.mcdx` ist jetzt für Mathcad Prime 11.0.0.0 gestempelt und öffnet damit
auch in allen neueren Versionen. Prime vergleicht beim Öffnen nur die Formatversion in `docProps/app.xml`
(`serializationVersion`) mit seiner eigenen und lehnt neuere ab („…because it is from a more recent version
of Mathcad“). Prime 11.0.1 schreibt 11.0.0.1, Prime 12 schreibt 12.0.0.0; die Datei trägt jetzt 11.0.0.0.
Einstellungen und Versionsstempel stammen aus einem Prime-11-Arbeitsblatt; die drei Seitenattribute, die
erst Prime 12 kennt, sind entfernt. Erzeugen: `build_bericht2.py <ziel.mcdx> <Prime-11-Arbeitsblatt> generator/img`.
