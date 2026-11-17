# Rechenbericht Kompakte Kartfelge, Konzept 2 (Mathcad Prime)

`Rechenbericht_Kartfelge_Konzept2_Lenhard.mcdx` ist der Rechenbericht „Kompakte Kartfelge, Konzept 2
(neue Felge, Bestandsnabe)“ vom 11.11.2026 als rechnendes Mathcad-Prime-Arbeitsblatt. Aufbau wie im
Rechenbericht Pneumatik-Spanner: Deckblatt, Inhaltsverzeichnis, je Abschnitt zentrierte Überschrift,
nummerierte Teilschritte, `:=`-Definitionen mit Einheiten, Ergebnisse mit `=`, Nachweise als Vergleich.
Kopfzeile „Lenhard“, Fußzeile mit Datum und „Seite x von y“, A4, 18 Seiten.

Mathcad rechnet beim Öffnen alles selbst nach. Die Datei enthält keine gespeicherten Ergebnisse.

## Prüfung

- Jede Formel wurde beim Erzeugen mit Einheiten nachgerechnet, in der Reihenfolge, in der Prime auswertet
  (oben nach unten, links nach rechts). Es gibt keine undefinierten Variablen, keine Einheitenfehler und keine
  doppelten Definitionen. Alle Werte stehen in `Pruefprotokoll.txt`.
- Die Plattenbeiwerte der Radscheibe (β = 0,569 eingespannt, 0,855 gelenkig, Axiallast 0,226 / 0,437) und
  der Kippwinkel wurden unabhängig mit der Kirchhoff-Plattentheorie nachgerechnet (`generator/plate_check.py`).
- `worksheet.xml`, Kopf- und Fußzeile, alle Formeln, `result.xml` und `presentation.xml` sind gegen die
  XSD-Schemata worksheet50, math50, result10 und presentation10 gültig. Relationships und XAML-Pakete sind
  konsistent (`generator/validate.py`).
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
python generator/build_kartfelge.py <ziel.mcdx> <beliebiges Prime-11-Arbeitsblatt.mcdx> generator/img
python generator/validate.py <ziel.mcdx> <Ordner mit worksheet50.xsd usw.>
```

Das Prime-11-Arbeitsblatt liefert nur Versionsstempel und Standard-Formelstile. Benötigt: Python 3.10+,
matplotlib (Skizzen), sympy/numpy (nur `plate_check.py`), lxml (nur `validate.py`).
