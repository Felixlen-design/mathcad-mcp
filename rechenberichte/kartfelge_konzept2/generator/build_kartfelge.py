"""Rechenbericht Kompakte Kartfelge, Konzept 2 -> Mathcad Prime worksheet (.mcdx)."""
import re
import sys
import zipfile

from mathexpr import PI, Abs, Cmp, If, Num, Op, Paren, Root, Str, UOp, Unit, V, F, q
from mcdx_doc import (BASE_SIZE, BOM, CONTENT_W, MARGIN_B, MARGIN_L, MARGIN_R, MARGIN_T, PAGE_H, PAGE_W,
                      XML_DECL, D, DE, DF, Doc, E, IMG, Run, T, X, png_size, rel_id)

OUT = sys.argv[1]
REF = sys.argv[2]          # a Prime 11 worksheet to take version stamps and default styles from
IMGDIR = sys.argv[3]

CW = CONTENT_W
XS, XM, XR = 9.6, 28.8, 352.0
NOTE = 13.3333333333333
NOTE_S = 12.0
TITLE = 21.3333333333333
doc = Doc()


# ------------------------------------------------------------------ layout helpers
SIDE = {"left": None, "bottom": -1.0}   # right-hand image block: notes must stay left of it


def avail():
    return SIDE["left"] if doc.abs_y < SIDE["bottom"] else CW


def side_image(path, width):
    pw_, ph_ = png_size(path)
    h = width * ph_ / pw_
    doc.ensure(h + 30)
    doc.put(IMG(path, width, h), CW - width, doc.abs_y)
    SIDE["left"], SIDE["bottom"] = CW - width - 12, doc.abs_y + h
    return h


def end_side():
    if doc.abs_y < SIDE["bottom"]:
        doc.y += SIDE["bottom"] - doc.abs_y + 4
    SIDE["bottom"] = -1.0


def title(text, key, force=False):
    if doc.items and (force or doc.y > PAGE_H * 0.6):
        doc.new_page()
    elif doc.items:
        doc.skip(18)
    doc.mark(key)
    doc.row((0, T(text, CW, size=TITLE, align="Center")), gap=10)


def sub(text):
    doc.skip(4)
    doc.row((XS, T(text, avail() - XS, bold=True)), gap=3, keep=75)


def plain(text):
    if isinstance(text, str):
        return re.sub(r"(?<=[A-Za-zΔσφτ])_(?=[A-Za-z0-9])", "", text)
    if isinstance(text, Run):
        text.text = plain(text.text)
        return text
    return [plain(t) for t in text]


def note(text, x=XM, size=NOTE, gap=4, italic=False):
    text = plain(text)
    doc.row((x, T(text, avail() - x, size=size, italic=italic)), gap=gap)


def m(cell, text=None, x=XM, gap=None):
    """Math region at x with an optional comment in the right column (or below, if there is no room)."""
    kw = {} if gap is None else {"gap": gap}
    room = avail() == CW and cell.width() < XR - x - 10
    if text and room:
        doc.row((x, cell), (XR, T(plain(text), CW - XR, size=NOTE)), **kw)
    else:
        doc.row((x, cell), gap=1 if text else (gap or 4))
        if text:
            note(text, x=x + 24, italic=True)


def inp(*pairs):
    """Input definitions, two per row, each with a short comment."""
    cols = (XM, XM + 300)
    for i in range(0, len(pairs), 2):
        cells = []
        for x, (cell, txt) in zip(cols, pairs[i:i + 2]):
            cells.append((x, cell))
            if txt:
                cells.append((x + 128, T(plain(txt), 158 if x == cols[0] else CW - x - 128, size=NOTE_S)))
        doc.row(*cells)


def pair(c1, c2, x2=None):
    doc.row((XM, c1), (x2 or XM + 300, c2))


def label(text):
    doc.row((XM, T(plain(text), avail() - XM, size=NOTE, italic=True)), gap=1, keep=45)


Z0 = q(0, "N")
DIV12 = Op("div", 1, 2)

# ------------------------------------------------------------------ page 1: cover
doc.skip(40)
doc.row((0, T("Rechenbericht", CW, size=37.3333333333333, bold=True, align="Center")), gap=8)
doc.row((0, T("Kompakte Kartfelge", CW, size=TITLE, bold=True, align="Center")), gap=4)
doc.row((0, T("Konzept 2: neue Felge, Bestandsnabe", CW, size=17.3333333333333, align="Center")), gap=8)
doc.row((0, T("Lenhard", CW, size=BASE_SIZE, align="Center")), gap=40)
w_img = 560.0
pw, ph = png_size(f"{IMGDIR}/schnitt.png")
doc.row(((CW - w_img) / 2, IMG(f"{IMGDIR}/schnitt.png", w_img, w_img * ph / pw)), gap=6)
doc.row((0, T("Prinzipskizze kurvenäußeres Vorderrad, Halbschnitt (Maße in mm, x ab Felgenaußenkante)",
              CW, size=NOTE, align="Center", italic=True)), gap=40)
doc.row((0, T([["Grundlage: Rechenbericht Kompakte Kartfelge, Konzept 2, vom 11.11.2026."],
               ["Geschätzte Maße (aus Fotos) und Lastannahmen sind vor der Fertigung zu prüfen."]],
              CW, size=NOTE, align="Center")))

# ------------------------------------------------------------------ page 2: table of contents (filled in later)
doc.new_page()
doc.mark("toc")
doc.row((0, T("Inhaltsverzeichnis", CW, size=TITLE, bold=True, align="Center")), gap=30)
toc_top = doc.abs_y

# ------------------------------------------------------------------ 1 Eingangsdaten
title("1  Eingangsdaten", "s1", force=True)
note("Die Nabe bleibt unverändert, die Felge wird neu: Die Radscheibe sitzt nicht mehr in der Mitte "
     "(x = 81 … 91 mm), sondern außen bei x = 13 … 25 mm, sodass die Felge die 95 mm lange Nabe vollständig "
     "überdeckt. Breite und Reifensitz bleiben gleich. Die Koordinate x zählt in allen Rechnungen ab der "
     "Felgenaußenkante in Richtung Kart.", x=XS)
sub("1) Massen und Fahrzustand")
inp((D("m_K", q(110, "kg")), "Masse Kart (gegeben)"),
    (D("m_F", q(80, "kg")), "Masse Fahrer (gegeben)"),
    (D("g_E", q(9.81, "m/s^2")), "Erdbeschleunigung"),
    (D("φ_V", Num(0.43)), "Achslastanteil vorn (angenommen)"),
    (D("h_S", q(250, "mm")), "Schwerpunkthöhe (angenommen)"),
    (D("s_V", q(1050, "mm")), "Spurweite vorn (angenommen)"),
    (D("n_q", Num(1.5)), "Querbeschleunigung in g (angenommen)"),
    (D("f_St", Num(3)), "Stoß: Vielfaches der statischen Radlast"))
sub("2) Felge und Rad")
inp((D("b_F", q(148, "mm")), "Felgenbreite (Handskizze)"),
    (D("r_R", q(125, "mm")), "Reifenradius (angenommen)"),
    (D("x_S", q(25, "mm")), "Flanschfläche = Innenseite der Radscheibe"),
    (D("t_S", q(12, "mm")), "Dicke der neuen Radscheibe (x = 13 … 25)"))
m(DE("x_R", V("b_F") / 2, "mm"), "Radmitte = halbe Felgenbreite")
sub("3) Nabe und Achsschenkel (aus Fotos geschätzt)")
inp((D("x_A", q(24, "mm")), "Lagermitte A (außen), 2× Lager 6003"),
    (D("x_B", q(115, "mm")), "Lagermitte B (kartseitig)"),
    (D("x_Bu", q(120, "mm")), "Bund am Achsschenkel (Ø25)"),
    (D("x_L", q(205, "mm")), "Lenkachse (85 mm hinter dem Bund)"),
    (D("d_A", q(17, "mm")), "Durchmesser Achsschenkel"))
m(DE("a_A", V("x_R") - V("x_A"), "mm"), "Radmitte bis Lager A")
m(DE("b_B", V("x_B") - V("x_R"), "mm"), "Radmitte bis Lager B")
m(DE("l_L", V("x_B") - V("x_A"), "mm"), "Lagerabstand")
note("Flansch-Ø73, Lochkreis Ø58 (3× M8), Zentrierung Ø40 und die Nabenlänge von 95 mm sind ebenfalls aus "
     "Fotos geschätzt. Alle geschätzten Werte müssen am Bauteil nachgemessen werden (Abschnitt 9).",
     x=XS, italic=True)

# ------------------------------------------------------------------ 2 Lastannahmen
title("2  Lastannahmen", "s2")
note("Maßgebend ist das kurvenäußere Vorderrad bei 1,5 g Querbeschleunigung. Angenommen, weil nicht gemessen: "
     "Achslast vorn 43 %, Schwerpunkthöhe 250 mm, Spurweite vorn 1050 mm, halbe Radlastverlagerung an der "
     "Vorderachse, keine Vorderradbremse.", x=XS)
sub("1) Gewichtskraft und statische Radlast vorn")
m(DE("m_ges", V("m_K") + V("m_F"), "kg"), "Gesamtmasse")
m(DE("G_K", V("m_ges") * V("g_E"), "N", 1), "Gewichtskraft")
m(DE("F_zs", V("φ_V") * V("G_K") / 2, "N", 1), "statische Radlast vorn")
sub("2) Radlastverlagerung in der Kurve, davon die Hälfte an der Vorderachse")
m(DE("a_y", V("n_q") * V("g_E"), "m/s^2", 3), "Querbeschleunigung")
m(DE("ΔF_z", DIV12 * ((V("m_ges") * V("a_y") * V("h_S")) / V("s_V")), "N", 1))
m(DE("F_za", V("F_zs") + V("ΔF_z"), "N", 1), "kurvenäußeres Rad")
m(DE("F_zi", V("F_zs") - V("ΔF_z"), "N", 1), "kurveninneres Rad")
sub("3) Seitenkraft der Vorderachse, im Verhältnis der Radlasten aufgeteilt")
m(DE("F_yV", V("φ_V") * V("m_ges") * V("a_y"), "N", 1), "Seitenkraft Vorderachse")
m(DE("F_ya", V("F_yV") * V("F_za") / (2 * V("F_zs")), "N", 1), "kurvenäußeres Rad, nach innen (zum Kart)")
m(DE("F_yi", V("F_yV") * V("F_zi") / (2 * V("F_zs")), "N", 1), "kurveninneres Rad, nach außen")
sub("4) Stoß und Kippmoment")
m(DE("F_zSt", V("f_St") * V("F_zs"), "N", 1), "3 × statische Radlast")
m(DE("M_y", V("F_ya") * V("r_R"), "N*m", 1), "Kippmoment aus der Seitenkraft")
m(E(q(140, "mm") / V("r_R"), None, 2), "Ein Reifenradius von 140 statt 125 mm erhöht das Kippmoment um 12 %.")
sub("Lastfälle")
note([["1  Geradeaus:  F_z = F_zs,  F_y = 0"],
      ["2  Kurve, äußeres Rad:  F_z = F_za,  F_y = +F_ya (zum Kart)"],
      ["3  Kurve, inneres Rad:  F_z = F_zi,  F_y = −F_yi (nach außen)"],
      ["4  Stoß:  F_z = F_zSt,  F_y = 0"]])

# ------------------------------------------------------------------ 3 Lagerkräfte
title("3  Lagerkräfte", "s3")
side_image(f"{IMGDIR}/fkb.png", 245.0)
note("Die Bodenkräfte greifen 125 mm unter der Achse in der Radmitte an; die Radmitte liegt zwischen den "
     "Lagern. Momentengleichgewicht um Lager B bzw. Lager A ergibt die Lagerkräfte.", x=XS)
note("Vorzeichen: F_A und F_B positiv = der Achsschenkel drückt das Rad nach unten (Gegenkraft zur Radlast), "
     "negativ = nach oben. F_y positiv = zum Kart hin. Das Bild zeigt die Richtungen für Kurve außen.",
     x=XS, italic=True)
sub("1) Lagerkräfte als Funktion von F_z und F_y")
m(DF("F_A", ["F_z", "F_y"], (V("F_z") * V("b_B") - V("F_y") * V("r_R")) / V("l_L")), "Momente um Lager B")
m(DF("F_B", ["F_z", "F_y"], (V("F_z") * V("a_A") + V("F_y") * V("r_R")) / V("l_L")), "Momente um Lager A")
note("Kontrolle: F_A + F_B = F_z, weil a_A + b_B = l_L.")
end_side()
doc.row((0, T("Freikörperbild kurvenäußeres Rad: Kräfte auf Rad und Nabe", CW, size=NOTE_S, italic=True,
              align="Right")), gap=4)
sub("2) Lastfälle")
label("Lastfall 1: Geradeaus")
pair(DE("F_A1", F("F_A", V("F_zs"), Z0), "N", 1), DE("F_B1", F("F_B", V("F_zs"), Z0), "N", 1))
label("Lastfall 2: Kurve, äußeres Rad")
pair(DE("F_A2", F("F_A", V("F_za"), V("F_ya")), "N", 1), DE("F_B2", F("F_B", V("F_za"), V("F_ya")), "N", 1))
pair(DE("F_axB", V("F_ya"), "N", 1), E(V("F_A2") + V("F_B2"), "N", 1))
note("Axialkraft an Lager B; Kontrolle rechts: Summe = F_za.", x=XM + 20, italic=True)
label("Lastfall 3: Kurve, inneres Rad")
pair(DE("F_A3", F("F_A", V("F_zi"), -V("F_yi")), "N", 1), DE("F_B3", F("F_B", V("F_zi"), -V("F_yi")), "N", 1))
m(DE("F_axA", V("F_yi"), "N", 1), "Axialkraft nach außen, Lager A")
label("Lastfall 4: Stoß")
pair(DE("F_A4", F("F_A", V("F_zSt"), Z0), "N", 1), DE("F_B4", F("F_B", V("F_zSt"), Z0), "N", 1))
note("In der Kurve wirken die beiden Lagerkräfte entgegengesetzt, weil das Kippmoment aus der Seitenkraft "
     "überwiegt: Lager B trägt 1915 N, Lager A wird mit 1181 N nach oben belastet. Die Axialkraft ist Lager B "
     "zugeordnet, weil das kurvenäußere Rad nach innen gedrückt wird. Wie die Bestandsnabe die Axialkraft "
     "tatsächlich führt, ist nicht bekannt; die Zuordnung zu B ist der ungünstigere Fall, weil B bereits die "
     "größere Radiallast trägt.")

# ------------------------------------------------------------------ 4 Wälzlager
title("4  Wälzlager 6003", "s4")
note("Tragzahlen 6003 (17 × 35 × 10) nach SKF. Die Lagertypen selbst sind geschätzt und an der Nabe "
     "abzulesen.", x=XS)
inp((D("C_r", q(6.37, "kN")), "dynamische Tragzahl"),
    (D("C_0r", q(3.25, "kN")), "statische Tragzahl"),
    (D("f_0", Num(14)), "Berechnungsfaktor"))
sub("1) Äquivalente Last, Kurve außen")
m(DE("P_A", Abs(V("F_A2")), "N", 1), "Lager A: nur Radiallast")
m(DE("F_rB", V("F_B2"), "N", 1), "Lager B: Radiallast")
m(DE("f_a", V("f_0") * V("F_axB") / V("C_0r"), None, 2), "Eingangswert der SKF-Tabelle")
note("SKF-Tabelle (normale Lagerluft), linear interpoliert zwischen f0·Fa/C0 = 3,45 und 5,17:")
doc.row((XM, D("f_a1", Num(3.45))), (XM + 150, D("e_1", Num(0.38))), (XM + 300, D("Y_1", Num(1.15))))
doc.row((XM, D("f_a2", Num(5.17))), (XM + 150, D("e_2", Num(0.42))), (XM + 300, D("Y_2", Num(1.04))))
lin = (V("f_a") - V("f_a1")) / (V("f_a2") - V("f_a1"))
pair(DE("e_B", V("e_1") + (V("e_2") - V("e_1")) * lin, None, 3),
     DE("Y_B", V("Y_1") + (V("Y_2") - V("Y_1")) * lin, None, 3))
pair(E(V("F_axB") / V("F_rB"), None, 3), X(Cmp(V("F_axB") / V("F_rB"), ">", V("e_B"))), x2=XM + 190)
note("Fa / Fr ist größer als e, die Axiallast wird mit Y_B angesetzt.", x=XM + 20, italic=True)
m(DE("P_B", 0.56 * V("F_rB") + V("Y_B") * V("F_axB"), "N", 0))
sub("2) Nominelle Lebensdauer L10 in Mio. Umdrehungen")
pair(DE("L_10A", (V("C_r") / V("P_A")) ** 3, None, 1), DE("L_10B", (V("C_r") / V("P_B")) ** 3, None, 2))
note("Bei Dauer-Kurvenlast. Realistischer ist ein Lastkollektiv: 20 % der Zeit kurvenaußen (q_1), "
     "20 % kurveninnen (q_2), 60 % geradeaus (q_3).")
doc.row((XM, D("q_1", Num(0.2))), (XM + 150, D("q_2", Num(0.2))), (XM + 300, D("q_3", Num(0.6))))
m(DE("P_mA", Root(V("q_1") * V("P_A") ** 3 + V("q_2") * Abs(V("F_A3")) ** 3 + V("q_3") * V("F_A1") ** 3, 3), "N", 0))
m(DE("P_mB", Root(V("q_1") * V("P_B") ** 3 + V("q_2") * Abs(V("F_B3")) ** 3 + V("q_3") * V("F_B1") ** 3, 3), "N", 0))
note("Lager A, Kurve innen: die Axialkraft F_axA = 102 N ist vernachlässigt (Einfluss auf L10 etwa 1 %).",
     italic=True)
pair(DE("L_10mA", (V("C_r") / V("P_mA")) ** 3, None, 0), DE("L_10mB", (V("C_r") / V("P_mB")) ** 3, None, 1))
inp((D("v_1", q(50, "km/hr")), "mittlere Geschwindigkeit"),)
m(DE("n_1", V("v_1") / (2 * PI * V("r_R")), "1/min", 0), "Raddrehzahl bei 50 km/h")
mio = Op("pow", 10, 6)
pair(DE("L_hA", V("L_10mA") * mio / V("n_1"), "hr", 0), DE("L_hB", V("L_10mB") * mio / V("n_1"), "hr", 0))
pair(DE("s_A", V("L_10mA") * mio * 2 * PI * V("r_R"), "km", 0),
     DE("s_B", V("L_10mB") * mio * 2 * PI * V("r_R"), "km", 0))
sub("3) Statische Tragsicherheit")
m(DE("S_0A", V("C_0r") / V("P_A"), None, 2), "Lager A")
m(E(0.6 * V("F_rB") + 0.5 * V("F_axB"), "N", 0), "kleiner als F_rB, daher ist P0 = Fr maßgebend")
m(DE("S_0B", V("C_0r") / V("F_rB"), None, 2), "Lager B")
inp((D("f_RS", Num(1.3)), "Randsteinschlag in der Kurve"),)
m(DE("S_0BR", V("S_0B") / V("f_RS"), None, 2), "Lager B mit Randsteinschlag")
m(X(Cmp(V("S_0BR"), ">=", 1)), "gefordert S0 ≥ 1, bei Stößen üblicherweise ≥ 1,5")
sub("4) Drehzahl und Passungen")
inp((D("v_max", q(80, "km/hr")), "Höchstgeschwindigkeit"),
    (D("n_G", q(24000, "1/min")), "Grenzdrehzahl 6003 (SKF)"))
pair(DE("n_max", V("v_max") / (2 * PI * V("r_R")), "1/min", 0), X(Cmp(V("n_max"), "<", V("n_G"))))
note("Der Außenring läuft mit der Nabe um und sitzt fest; der Innenring steht auf dem Achsschenkel (Ø17 g6) "
     "und wird über die Distanzhülse axial geklemmt.")

# ------------------------------------------------------------------ 5 Achsschenkel
title("5  Achsschenkel Ø17", "s5")
note("Der Werkstoff des Kaufteils ist nicht bekannt; angenommen ist 42CrMo4 vergütet. Der Achsschenkel ist am "
     "Bund (x = 120 mm) eingespannt und wird an den Lagerstellen mit den Gegenkräften der Lagerkräfte belastet "
     "(positiv = nach oben).", x=XS)
inp((D("R_m", q(1000, "N/mm^2")), "Zugfestigkeit (angenommen)"),
    (D("R_e", q(750, "N/mm^2")), "Streckgrenze (angenommen)"))
sub("1) Schnittgrößen")
m(DF("M_LB", ["F_1"], V("F_1") * V("l_L")), "Moment an Lager B")
m(DF("M_Bu", ["F_1", "F_2"], V("F_1") * (V("x_Bu") - V("x_A")) + V("F_2") * (V("x_Bu") - V("x_B"))),
  "Moment am Bund")
for i, lab in ((1, "Geradeaus"), (2, "Kurve, äußeres Rad"), (3, "Kurve, inneres Rad"), (4, "Stoß")):
    label(f"Lastfall {i}: {lab}")
    pair(DE(f"M_B{i}", F("M_LB", V(f"F_A{i}")), "N*m", 1),
         DE(f"M_Bu{i}", F("M_Bu", V(f"F_A{i}"), V(f"F_B{i}")), "N*m", 1), x2=XM + 250)
sub("2) Spannungen, Kurve außen")
pair(DE("W_A", PI * V("d_A") ** 3 / 32, "mm^3", 1), DE("A_A", PI * V("d_A") ** 2 / 4, "mm^2", 1))
m(DE("σ_bB", Abs(V("M_B2")) / V("W_A"), "N/mm^2", 1), "Biegung an Lager B")
m(DE("σ_bBu", Abs(V("M_Bu2")) / V("W_A"), "N/mm^2", 1), "Biegung am Bund")
m(DE("τ_Q", Op("div", 4, 3) * (Abs(V("F_A2")) / V("A_A")), "N/mm^2", 1),
  "größte Querkraft zwischen den Lagern = |F_A2|")
m(DE("σ_ax", V("F_axB") / V("A_A"), "N/mm^2", 1), "Druck aus der Axialkraft")
note("Schub- und Druckspannung sind gegenüber der Biegespannung vernachlässigbar.", italic=True)
sub("3) Statischer Nachweis mit Stoßfaktor 1,5 auf die Kurvenlast")
inp((D("f_S", Num(1.5)), "Stoßfaktor"),)
m(DE("σ_max", V("f_S") * V("σ_bB"), "N/mm^2", 1), "größte Biegespannung mit Stoßfaktor")
m(DE("S_F", V("R_e") / V("σ_max"), None, 2), "Sicherheit gegen Fließen")
sub("4) Dauerfestigkeitsnachweis am Bund")
note("Der Achsschenkel dreht nicht mit. Das Moment am Bund schwankt deshalb zwischen Geradeausfahrt (M_Bu1) "
     "und Kurve (M_Bu2).")
pair(DE("M_m", Abs(V("M_Bu1") + V("M_Bu2")) / 2, "N*m", 1), DE("M_a", Abs(V("M_Bu1") - V("M_Bu2")) / 2, "N*m", 1))
pair(DE("σ_m", V("M_m") / V("W_A"), "N/mm^2", 1), DE("σ_a", V("M_a") / V("W_A"), "N/mm^2", 1))
m(DE("σ_bW", 0.5 * V("R_m"), "N/mm^2", 0), "Biegewechselfestigkeit ≈ 0,5 · Rm")
inp((D("K_1", Num(0.95)), "Größeneinfluss"), (D("K_2", Num(0.9)), "Oberflächeneinfluss"),
    (D("β_k", Num(1.8)), "Kerbwirkungszahl Wellenabsatz"))
m(DE("σ_GW", V("σ_bW") * V("K_1") * V("K_2") / V("β_k"), "N/mm^2", 1), "Gestaltfestigkeit")
m(DE("σ_GA", V("σ_GW") * (1 - V("σ_m") / V("R_m")), "N/mm^2", 1), "Mittelspannungskorrektur (Goodman)")
pair(DE("S_D", V("σ_GA") / V("σ_a"), None, 2), X(Cmp(V("S_D"), ">=", 1.5)), x2=XM + 190)
note("Überschlägiger Nachweis mit Mittelspannungskorrektur nach Goodman, kein vollständiger Nachweis nach "
     "DIN 743. Er ist konservativ, weil die volle Kurvenlast als Dauerlast angesetzt ist.", italic=True)
sub("5) Erforderlicher Durchmesser bei Sicherheit 1,5")
inp((D("S_erf", Num(1.5)), "geforderte Sicherheit"),)
m(DE("d_erfS", Root(32 * V("f_S") * Abs(V("M_B2")) * V("S_erf") / (PI * V("R_e")), 3), "mm", 1),
  "statisch (vorhanden 17 mm)")
m(DE("W_erf", (V("S_erf") * V("M_a") + V("σ_GW") * V("M_m") / V("R_m")) / V("σ_GW"), "mm^3", 1),
  "aus S_D = S_erf nach W aufgelöst")
m(DE("d_erfD", Root(32 * V("W_erf") / PI, 3), "mm", 1), "dauerfest (vorhanden 17 mm)")
label("Variante: Stahl mit nur Rm ≈ 700 N/mm²")
inp((D("R_m7", q(700, "N/mm^2")), "Zugfestigkeit Variante"),)
m(DE("σ_GW7", 0.5 * V("R_m7") * V("K_1") * V("K_2") / V("β_k"), "N/mm^2", 1))
m(DE("S_D7", V("σ_GW7") * (1 - V("σ_m") / V("R_m7")) / V("σ_a"), None, 2), "Ø17 reicht dann nicht")
m(DE("W_20", PI * q(20, "mm") ** 3 / 32, "mm^3", 1), "Ø20")
m(DE("S_D20", V("σ_GW7") * (1 - V("M_m") / (V("W_20") * V("R_m7"))) / (V("M_a") / V("W_20")), None, 2),
  "mit Ø20 wieder ausreichend")
sub("6) Bearbeitung")
note("Der Schaft Ø17 wird von etwa 120 auf 102,5 mm gekürzt und erhält ein neues Gewinde von 14 mm Länge. "
     "Achsmutter und Scheibe liegen dann 3,5 mm hinter der Felgenaußenkante. Im Gewindebereich wirkt kein "
     "Biegemoment, weil er außerhalb von Lager A liegt.")

# ------------------------------------------------------------------ 6 Neue Felge
title("6  Neue Felge", "s6")
note("Werkstoff EN AW-6082 T6: Rm ≥ 310 N/mm² und Rp0,2 ≥ 260 N/mm² für Rundstangen von 20 bis 150 mm "
     "(Datenblatt Metall Service Menziken).", x=XS)
inp((D("R_mAl", q(310, "N/mm^2")), "Zugfestigkeit"), (D("R_p02", q(260, "N/mm^2")), "Dehngrenze"))
sub("1) Kippmoment an der Radscheibe")
m(DE("e_S", V("x_R") - V("x_S"), "mm"), "Flanschfläche liegt 49 mm außerhalb der Radmitte")
m(DE("M_K", V("F_ya") * V("r_R") + V("F_za") * V("e_S"), "N*m", 1), "Radlast und Seitenkraft drehen gleich")
inp((D("x_Salt", q(91, "mm")), "alte Felge: Scheibe innerhalb der Radmitte"),)
m(DE("M_Kalt", V("F_ya") * V("r_R") + V("F_za") * (V("x_R") - V("x_Salt")), "N*m", 1),
  "dort wirkt die Radlast entlastend")
m(E(V("M_K") / V("M_Kalt"), None, 2), "das neue Moment ist 39 % größer")
sub("2) Radscheibe als Kreisringplatte")
note("Die Scheibe ist zwischen Flanschrand und Felgenwand frei. Gerechnet ist eine Kreisringplatte mit starrem "
     "Kern unter Kippmoment (Kirchhoff-Platte, Ansatz w = W(r)·cos θ, ν = 0,33), einmal mit eingespanntem und "
     "einmal mit gelenkig gelagertem Außenrand. Die wirkliche Felgenwand liegt dazwischen. Für den gelenkigen "
     "Rand stimmt die Lösung mit den Tabellenwerten nach Roark überein.")
inp((D("r_a", q(55.3, "mm")), "Radius Felgenwand"),)
m(DE("r_i", q(73, "mm") / 2, "mm", 1), "Radius Flanschrand (Flansch-Ø73)")
m(E(V("r_i") / V("r_a"), None, 2), "Radienverhältnis")
inp((D("β_ein", Num(0.569)), "Beiwert, Außenrand eingespannt"),
    (D("β_gel", Num(0.855)), "Beiwert, Außenrand gelenkig"))
m(DF("σ_S", ["t_x", "β_x"], V("β_x") * V("M_K") / (V("r_a") * V("t_x") ** 2)), "Biegespannung am Flanschrand")
pair(DE("σ_Sein", F("σ_S", V("t_S"), V("β_ein")), "N/mm^2", 1),
     DE("σ_Sgel", F("σ_S", V("t_S"), V("β_gel")), "N/mm^2", 1))
note("Weil die Felge umläuft, wechselt diese Spannung bei jeder Radumdrehung das Vorzeichen. "
     "Zulässige Spannung (Richtwerte, nicht nachgeschlagen):")
m(DE("σ_bWAl", 0.3 * V("R_mAl"), "N/mm^2", 0), "Biegewechselfestigkeit ≈ 0,3 · Rm")
inp((D("K_Al", Num(0.85)), "Oberflächen- und Größeneinfluss"),
    (D("β_kAl", Num(2)), "Kerbwirkung Ausrundung, Bolzenlöcher"))
m(DE("σ_zulS", V("σ_bWAl") * V("K_Al") / V("β_kAl"), "N/mm^2", 1))
pair(DE("S_Sein", V("σ_zulS") / V("σ_Sein"), None, 2), DE("S_Sgel", V("σ_zulS") / V("σ_Sgel"), None, 2))
label("Vergleich Scheibendicke 10 mm und 14 mm (eingespannt | gelenkig):")
pair(E(F("σ_S", q(10, "mm"), V("β_ein")), "N/mm^2", 1), E(F("σ_S", q(10, "mm"), V("β_gel")), "N/mm^2", 1))
pair(E(F("σ_S", q(14, "mm"), V("β_ein")), "N/mm^2", 1), E(F("σ_S", q(14, "mm"), V("β_gel")), "N/mm^2", 1))
note("10 mm ergäbe nur Sicherheit 1,5 bis 2,2; mit 12 mm bleibt sie auch im ungünstigen Fall über 2.",
     italic=True)
label("Axialkraft (Kreisringplatte unter Axiallast, Beiwerte ebenfalls nachgerechnet):")
doc.row((XM, D("β_Fein", Num(0.226))), (XM + 300, D("β_Fgel", Num(0.437))))
pair(DE("σ_axSe", V("β_Fein") * V("F_ya") / V("t_S") ** 2, "N/mm^2", 1),
     DE("σ_axSg", V("β_Fgel") * V("F_ya") / V("t_S") ** 2, "N/mm^2", 1))
note("Unter dem Kippmoment kippt die Scheibe um 0,0016° (eingespannt) bis 0,0041° (gelenkig), also um weniger "
     "als 0,005° (E = 70 000 N/mm²).", italic=True)
sub("3) Felgenwand")
note("Der Reifen stützt sich an beiden Wülsten ab. In der Kurve trägt die kartseitige Wulst den größeren Teil "
     "der Radlast, dazu drückt die Seitenkraft auf das kartseitige Horn. Die Felgenwand leitet das als "
     "Biegemoment zur Scheibe.")
inp((D("x_W1", q(11.5, "mm")), "Mitte Reifensitz außen (x = 5 … 18)"),
    (D("x_W2", q(136.5, "mm")), "Mitte Reifensitz kartseitig (130 … 143)"),
    (D("r_H", q(65, "mm")), "Angriffsradius der Seitenkraft am Horn"),
    (D("s_W", q(4, "mm")), "Wandstärke Felge (angenommen)"))
m(DE("F_W2", (V("F_za") * (V("x_R") - V("x_W1")) + V("F_ya") * (V("r_R") - V("r_H"))) / (V("x_W2") - V("x_W1")),
     "N", 0), "Wulstkraft kartseitig (Momente um die äußere Wulst)")
m(DF("M_W", ["x"], V("F_W2") * (V("x_W2") - V("x")) + V("F_ya") * V("r_H")), "Biegemoment im Schnitt x")
m(DF("W_W", ["r"], PI * V("r") ** 2 * V("s_W")), "Widerstandsmoment dünnwandiges Rohr")
cone = (q(126, "mm") - (q(126, "mm") - q(89, "mm")) * (V("x_S") - q(18, "mm")) / (q(60, "mm") - q(18, "mm")))
m(DE("r_W1", cone / 2 - V("s_W") / 2, "mm", 1), "Wandmitte am Scheibenübergang (Kegel Ø126 auf Ø89)")
m(DE("r_W2", q(89, "mm") / 2 - V("s_W") / 2, "mm", 1), "Wandmitte Tiefbett Ø89")
label("Scheibenübergang x = 25 mm, Tiefbett x = 60 mm und x = 100 mm:")
doc.row((XM, E(F("M_W", V("x_S")), "N*m", 1)), (XM + 195, E(F("M_W", q(60, "mm")), "N*m", 1)),
        (XM + 395, E(F("M_W", q(100, "mm")), "N*m", 1)))
m(DE("σ_W1", F("M_W", V("x_S")) / F("W_W", V("r_W1")), "N/mm^2", 1))
m(DE("σ_W2", F("M_W", q(60, "mm")) / F("W_W", V("r_W2")), "N/mm^2", 1))
m(DE("σ_W3", F("M_W", q(100, "mm")) / F("W_W", V("r_W2")), "N/mm^2", 1))
note("Diese Balkenrechnung erfasst nur die globale Biegung. Die örtliche Verformung der 123 mm frei "
     "auskragenden Wand unter der Wulstlast ist damit nicht nachgewiesen.", italic=True)
sub("4) Masse")
inp((D("ρ_Al", q(2700, "kg/m^3")), "Dichte Aluminium"), (D("r_Si", q(20, "mm")), "Bohrung (Zentrierung Ø40)"),
    (D("r_So", q(58, "mm")), "Außenradius neue Scheibe"), (D("r_Soalt", q(40.5, "mm")), "alte Scheibe (Tiefbett innen)"),
    (D("t_Salt", q(10, "mm")), "Dicke alte Scheibe"))
m(DE("Δm", V("ρ_Al") * PI * Paren((V("r_So") ** 2 - V("r_Si") ** 2) * V("t_S")
                                  - (V("r_Soalt") ** 2 - V("r_Si") ** 2) * V("t_Salt")), "kg", 2))
note("Aus den Schnittkonturen ergibt sich für die neue Felge etwa 0,93 kg gegenüber 0,72 kg für die alte "
     "(beide mit 4 mm Wand). Das Mehrgewicht von rund 0,2 kg steckt in der größeren Scheibe.")

# ------------------------------------------------------------------ 7 Radbolzen
title("7  Radbolzen 3× M8", "s7")
note("Angenommen sind Stehbolzen M8 der Festigkeitsklasse 8.8, Anziehmoment 20 N·m und ein Kraftverhältnis "
     "von 0,2.", x=XS)
inp((D("d_S", q(8, "mm")), "Nenndurchmesser"), (D("A_s", q(36.6, "mm^2")), "Spannungsquerschnitt"),
    (D("R_eS", q(640, "N/mm^2")), "Streckgrenze 8.8"), (D("M_A", q(20, "N*m")), "Anziehmoment"),
    (D("Φ_K", Num(0.2)), "Kraftverhältnis"), (D("n_S", Num(3)), "Anzahl Bolzen"))
m(DE("R_LK", q(58, "mm") / 2, "mm"), "Lochkreisradius (Lochkreis Ø58)")
sub("1) Bolzenkraft aus dem Kippmoment")
note("Drei Bolzen auf dem Lochkreis, Kippachse durch die Mitte (konservativ, ohne Abstützung am Flanschrand): "
     "Σ y² = 3/2 · R².")
m(DE("F_Bmax", V("M_K") * V("R_LK") / (Op("div", 3, 2) * V("R_LK") ** 2), "N", 0), "höchstbelasteter Bolzen")
sub("2) Vorspannung")
m(DE("F_V", V("M_A") / (0.2 * V("d_S")), "N", 0), "Faustformel F_V ≈ M_A / (0,2 · d)")
pair(DE("σ_V", V("F_V") / V("A_s"), "N/mm^2", 1), E(V("σ_V") / V("R_eS"), None, 2), x2=XM + 250)
note("Das sind 53 % der Streckgrenze von 640 N/mm².", x=XM + 20, italic=True)
sub("3) Klaffen")
m(DE("F_KR", V("F_V") - (1 - V("Φ_K")) * V("F_Bmax"), "N", 0), "Restklemmkraft, Fuge bleibt geschlossen")
m(DE("S_K", V("F_V") / ((1 - V("Φ_K")) * V("F_Bmax")), None, 2), "Sicherheit gegen Klaffen")
inp((D("α_A", Num(1.6)), "Anziehfaktor (Drehmomentschlüssel)"),)
pair(DE("F_KRmin", V("F_V") / V("α_A") - (1 - V("Φ_K")) * V("F_Bmax"), "N", 0),
     X(Cmp(V("F_KRmin"), ">", q(0, "N"))), x2=XM + 340)
note("Auch bei der kleinsten Vorspannung aus der Anziehstreuung bleibt die Fuge geschlossen.", x=XM + 20,
     italic=True)
sub("4) Dauerhaltbarkeit")
m(DE("σ_aS", V("Φ_K") * V("F_Bmax") / (2 * V("A_s")), "N/mm^2", 1), "Spannungsausschlag")
nmm2 = UOp("div", Unit("N"), UOp("pow", Unit("mm"), Num(2)))
m(DE("σ_ASV", 0.85 * Paren(q(150, "mm") / V("d_S") + 45) * nmm2, "N/mm^2", 1),
  "Ausschlagfestigkeit nach VDI 2230 (schlussvergütet)")
m(DE("S_DS", V("σ_ASV") / V("σ_aS"), None, 2), "Sicherheit Dauerhaltbarkeit")
sub("5) Rutschen")
inp((D("μ_T", Num(0.15)), "Reibwert in der Trennfuge"),)
m(DE("F_R", V("μ_T") * (V("n_S") * V("F_V") + V("F_ya")), "N", 0),
  "die Seitenkraft drückt die Felge zusätzlich gegen den Flansch")
m(DE("S_R", V("F_R") / V("F_zSt"), None, 2), "gegen die Stoß-Radlast (1202 N)")
sub("6) Flächenpressung unter der Mutter")
inp((D("d_h", q(9, "mm")), "Durchgangsbohrung"), (D("d_wF", q(17, "mm")), "Auflage-Ø Flanschmutter"),
    (D("d_wS", q(12.5, "mm")), "Auflage-Ø Sechskantmutter"))
pair(DE("A_pF", PI / 4 * (V("d_wF") ** 2 - V("d_h") ** 2), "mm^2", 1),
     DE("A_pS", PI / 4 * (V("d_wS") ** 2 - V("d_h") ** 2), "mm^2", 1))
pair(DE("p_F", V("F_V") / V("A_pF"), "N/mm^2", 1), DE("p_S", V("F_V") / V("A_pS"), "N/mm^2", 1))
m(DE("p_G", V("R_p02"), "N/mm^2", 0), "Grenzflächenpressung, konservativ = Rp0,2")
pair(DE("S_pF", V("p_G") / V("p_F"), None, 2), DE("S_pS", V("p_G") / V("p_S"), None, 2))
note("Mit Sechskantmutter ohne Scheibe liegt die Pressung zu nah an der Grenze. Auf der Aluminiumscheibe sind "
     "deshalb Flanschmuttern oder Scheiben nötig.")
sub("7) Länge der Stehbolzen")
pair(DE("l_St", V("t_S") + q(8, "mm") + q(3, "mm"), "mm"), X(Cmp(V("l_St"), "<=", V("x_S"))), x2=XM + 250)
note("Scheibe 12 mm + Mutter 8 mm + 3 mm Überstand. Bis 25 mm bleiben die Bolzen hinter der "
     "Felgenaußenkante. Die vorhandene Länge ist aus den Fotos auf etwa 22 mm geschätzt und muss gemessen "
     "werden.", x=XM + 20, italic=True)

# ------------------------------------------------------------------ 8 Vergleich Ist-Zustand
title("8  Vergleich mit dem Ist-Zustand", "s8")
note("Das Rad rückt 66 mm näher an die Lenkachse. Ist-Zustand gerechnet mit Lagermitten bei x = 90 und "
     "181 mm, Bund bei x = 186 mm und Lenkachse bei x = 271 mm, gleiche Lastannahmen.", x=XS)
doc.row((XM, D("x_Aalt", q(90, "mm"))), (XM + 145, D("x_Balt", q(181, "mm"))),
        (XM + 290, D("x_Bualt", q(186, "mm"))), (XM + 435, D("x_Lalt", q(271, "mm"))))
m(DF("F_Aalt", ["F_z", "F_y"],
     (V("F_z") * (V("x_Balt") - V("x_R")) - V("F_y") * V("r_R")) / (V("x_Balt") - V("x_Aalt"))))
m(DF("F_Balt", ["F_z", "F_y"],
     (V("F_z") * (V("x_R") - V("x_Aalt")) + V("F_y") * V("r_R")) / (V("x_Balt") - V("x_Aalt"))))
m(DF("M_Bualt", ["F_1", "F_2"],
     V("F_1") * (V("x_Bualt") - V("x_Aalt")) + V("F_2") * (V("x_Bualt") - V("x_Balt"))))
label("Lagerkräfte Kurve außen und Stoß, Moment am Bund")
pair(DE("F_A2alt", F("F_Aalt", V("F_za"), V("F_ya")), "N", 1), DE("F_B2alt", F("F_Balt", V("F_za"), V("F_ya")), "N", 1))
pair(DE("F_A4alt", F("F_Aalt", V("F_zSt"), Z0), "N", 1), DE("F_B4alt", F("F_Balt", V("F_zSt"), Z0), "N", 1))
m(DE("M_Bu2alt", F("M_Bualt", V("F_A2alt"), V("F_B2alt")), "N*m", 1), "Bund, Kurve")
m(DE("M_Bu4alt", F("M_Bualt", V("F_A4alt"), V("F_B4alt")), "N*m", 1), "Bund, Stoß")
label("Moment an der Lenkachse (Radlast mal Hebel Radmitte–Lenkachse)")
pair(DE("M_L1", V("F_zs") * (V("x_L") - V("x_R")), "N*m", 1), DE("M_L1alt", V("F_zs") * (V("x_Lalt") - V("x_R")), "N*m", 1))
pair(DE("M_L4", V("F_zSt") * (V("x_L") - V("x_R")), "N*m", 1),
     DE("M_L4alt", V("F_zSt") * (V("x_Lalt") - V("x_R")), "N*m", 1))
doc.ensure(330)
sub("Gegenüberstellung")
c1, c2, c3 = XS, 255.0, 430.0
doc.row((c1, T("Größe", 230, size=NOTE, bold=True)), (c2, T("Ist", 150, size=NOTE, bold=True)),
        (c3, T("Konzept 2", 150, size=NOTE, bold=True)), gap=3)
rows = [
    ("Lenkachse bis Felgeninnenkante", E(V("x_Lalt") - V("b_F"), "mm", 0), E(V("x_L") - V("b_F"), "mm", 0)),
    ("Lenkachse bis Radmitte", E(V("x_Lalt") - V("x_R"), "mm", 0), E(V("x_L") - V("x_R"), "mm", 0)),
    ("Größte Lagerkraft, Kurve", E("F_B2alt", "N", 0), E("F_B2", "N", 0)),
    ("Größte Lagerkraft, Stoß", E("F_A4alt", "N", 0), E("F_B4", "N", 0)),
    ("Moment am Bund, Kurve", E(Abs(V("M_Bu2alt")), "N*m", 0), E(Abs(V("M_Bu2")), "N*m", 0)),
    ("Moment am Bund, Stoß", E("M_Bu4alt", "N*m", 0), E("M_Bu4", "N*m", 0)),
    ("Moment Lenkachse, geradeaus", E("M_L1alt", "N*m", 0), E("M_L1", "N*m", 0)),
    ("Moment Lenkachse, Stoß", E("M_L4alt", "N*m", 0), E("M_L4", "N*m", 0)),
    ("Kippmoment Radscheibe, Kurve", E("M_Kalt", "N*m", 0), E("M_K", "N*m", 0)),
]
for lab, a, b in rows:
    doc.row((c1, T(lab, 235, size=NOTE)), (c2, a), (c3, b), gap=2)
doc.skip(6)
note("Im Ist-Zustand liegt die Radmitte außerhalb beider Lager. Die Radlast erzeugt dort ein großes Moment, das "
     "in der Kurve dem Kippmoment aus der Seitenkraft entgegenwirkt. Im Konzept fällt dieser Ausgleich weg; "
     "Kurvenlasten an Lager und Achsschenkel werden höher, dafür sinken die Stoßlasten an Lager und Bund auf "
     "weniger als die Hälfte. Die Lager des Achsschenkelbolzens und die Schweißnaht am Achsschenkel werden "
     "entlastet; nachgerechnet sind sie nicht, weil ihre Maße fehlen.", x=XS)

# ------------------------------------------------------------------ 9 Ergebnis
title("9  Ergebnisübersicht", "s9", force=True)
note("Alle Werte werden von Mathcad aus den vorangehenden Abschnitten übernommen.", x=XS, italic=True)
m(DF("Nachweis", ["S_x", "S_min"], If(Cmp(V("S_x"), ">=", V("S_min")), Str("erfüllt"), Str("nicht erfüllt"))),
  "Bewertung: Sicherheit S_x gegen Mindestwert S_min")
c1, c2, c3 = XS, 234.0, 368.0
doc.row((c1, T("Nachweis", 210, size=NOTE, bold=True)), (c2, T("Sicherheit", 130, size=NOTE, bold=True)),
        (c3, T("Bewertung (Mindestwert)", 250, size=NOTE, bold=True)), gap=3)
res = [
    ("Lager A, statisch", "S_0A", 1),
    ("Lager B, statisch", "S_0B", 1),
    ("Lager B mit Randsteinschlag", "S_0BR", 1),
    ("Achsschenkel Ø17, statisch", "S_F", 1.5),
    ("Achsschenkel Ø17, dauerfest", "S_D", 1.5),
    ("Radscheibe 12 mm, gelenkig", "S_Sgel", 1.5),
    ("Radscheibe 12 mm, eingespannt", "S_Sein", 1.5),
    ("Radbolzen, Klaffen", "S_K", 1),
    ("Radbolzen, Dauerhaltbarkeit", "S_DS", 1.5),
    ("Radbolzen, Rutschen (Stoß)", "S_R", 1),
    ("Flächenpressung Flanschmutter", "S_pF", 1),
]
for lab, s_name, smin in res:
    doc.row((c1, T(lab, 220, size=NOTE)), (c2, E(s_name, None, 2)),
            (c3, E(F("Nachweis", V(s_name), Num(smin)))), gap=2)
doc.row((c1, T("Felgenwand, globale Biegung", 220, size=NOTE)), (c2, E(V("σ_zulS") / V("σ_W2"), None, 1)),
        (c3, E(F("Nachweis", V("σ_zulS") / V("σ_W2"), Num(1.5)))), gap=2)
doc.row((c1, T("Lager B, Lebensdauer (Kollektiv)", 220, size=NOTE)), (c2, E("s_B", "km", 0)),
        (c3, T("nominell, bei 50 km/h", 220, size=NOTE)), gap=8)
note("Konzept 2 trägt rechnerisch: Alle geführten Nachweise sind erfüllt. Die kleinsten Reserven liegen bei "
     "Lager B (statisch 1,70, mit Randsteinschlag 1,31) und beim Achsschenkel Ø17 (Dauersicherheit 1,7, "
     "nur mit vergütetem Stahl Rm ≈ 1000 N/mm²). Der Abstand Lenkachse–Felgeninnenkante sinkt von 123 auf "
     "57 mm.", x=XS)
note("Gegenüber der ersten Abschätzung hat sich ein Wert geändert: Die Biegespannung in der Radscheibe beträgt "
     "12 bis 19 N/mm², nicht 63 N/mm². Die frühere Zahl war eine sehr grobe Obergrenze; die Plattenrechnung in "
     "Abschnitt 6 ist genauer. Die Scheibendicke von 12 mm bleibt.", x=XS)
doc.ensure(420)
sub("Grenzen der Rechnung")
note([["Die Rechnung ist ein Vorentwurf: Sie beruht auf Lastannahmen und auf Maßen, die zum Teil aus Fotos "
       "geschätzt sind."],
      [Run("•  Nicht nachgewiesen: ", bold=True, size=NOTE),
       Run("örtliche Beanspruchung der auskragenden Felgenwand, Lager und Schweißnaht des Achsschenkelbolzens, "
           "Freigang zum Chassis bei vollem Lenkeinschlag.", size=NOTE)],
      [Run("•  Vereinfacht: ", bold=True, size=NOTE),
       Run("Radscheibe als ideale Kreisringplatte, Dauerfestigkeit des Achsschenkels überschlägig, Lastkollektiv "
           "geschätzt.", size=NOTE)],
      [Run("•  Ventil: ", bold=True, size=NOTE),
       Run("sitzt im kartseitigen Kegel der Felge und ist nur von der Kartseite erreichbar, weil die Scheibe die "
           "Außenseite verschließt.", size=NOTE)],
      [Run("•  Zulassung: ", bold=True, size=NOTE),
       Run("Eine selbst gefertigte Felge hat keine FIA-Homologation.", size=NOTE)]], x=XS)
doc.ensure(150)
sub("Vor der Fertigung zu klären")
doc.row((XS, T([["☐  Lagertypen an der Nabe ablesen"],
                ["☐  Nabenlänge, Flansch-Ø, Zentrier-Ø, Lochkreis messen"],
                ["☐  Stehbolzenlänge messen (mind. 23 mm nötig)"],
                ["☐  Achsschenkel-Ø, Gewinde, Abstand Lenkachse–Bund"],
                ["☐  Werkstoff des Achsschenkels klären"]], 300, size=NOTE_S)),
        (XS + 305, T([["☐  Kartseitige Felgenkontur und Wandstärke messen"],
                      ["☐  Reifenradius, Spurweite, Schwerpunkthöhe und Achslastverteilung ermitteln"],
                      ["☐  Felge mit FEM nachrechnen (Scheibenübergang, Felgenwand)"],
                      ["☐  Freigang bei vollem Lenkeinschlag prüfen"]], CW - XS - 305, size=NOTE_S)))

# ------------------------------------------------------------------ table of contents
last_page = doc.page + 1
order = [("s1", "1  Eingangsdaten"), ("s2", "2  Lastannahmen"), ("s3", "3  Lagerkräfte"),
         ("s4", "4  Wälzlager 6003"), ("s5", "5  Achsschenkel Ø17"), ("s6", "6  Neue Felge"),
         ("s7", "7  Radbolzen 3× M8"), ("s8", "8  Vergleich mit dem Ist-Zustand"),
         ("s9", "9  Ergebnisübersicht, Grenzen, offene Punkte")]
entries = [("Deckblatt", "Seite 1"), ("Inhaltsverzeichnis", "Seite 2")]
for i, (key, text) in enumerate(order):
    start = doc.marks[key]
    end = (doc.marks[order[i + 1][0]] - 1) if i + 1 < len(order) else last_page
    entries.append((text, f"Seite {start}" if end == start else f"Seite {start}–{end}"))
y = toc_top + 20
for text, page in entries:
    dots = max(3, int((400 - len(text) * BASE_SIZE * 0.56) / (BASE_SIZE * 0.33)))
    doc.put(T(text + " " + "." * dots, 488), 0.0, y)
    doc.put(T(page, 110), 495.0, y)
    y += 34

# ------------------------------------------------------------------ header / footer
hdr_w = 150.0
hdr_left = PAGE_W - MARGIN_R - hdr_w
doc.header.append((T("Lenhard", hdr_w, align="Right"), 26.0, hdr_left))
doc.footer.append((T("Dienstag, 17. November 2026", 260), 26.0, MARGIN_L))
doc.footer_page_field = ("Seite_@PageNo_von_@PagesTotal", PAGE_W - MARGIN_R - 105, 26.0, 105.0)

# ------------------------------------------------------------------ check, then write
env, results, errors = doc.evaluate()
over = doc.overlaps()


def ident(c):
    return getattr(c, "name", None) or getattr(c, "kind", "text")


print(f"Seiten: {last_page}, Regionen: {len(doc.items)}, Ergebnisse: {len(results)}")
for it, val, shown in results:
    c = it.cell
    lhs = c.name if c.kind == "defeval" else "(Ausdruck)"
    print(f"  S.{it.page + 1:2d}  {lhs:10s} = {shown}")
print("Fehler:", errors if errors else "keine")
print("Überlappungen:", len(over))
for a, b in over:
    print("   ", a.page + 1, round(a.top, 1), round(a.left, 1), type(a.cell).__name__, ident(a.cell), "<->",
          round(b.top, 1), round(b.left, 1), type(b.cell).__name__, ident(b.cell))
names = [it.cell.name for it in doc.items if hasattr(it.cell, "name") and it.cell.name and
         it.cell.kind in ("define", "defeval", "fdefine")]
dups = {n for n in names if names.count(n) > 1}
print("Doppelt definiert:", dups or "keine")
if errors or dups:
    sys.exit(1)

# ------------------------------------------------------------------ base parts from a Prime 11 worksheet
ref = zipfile.ZipFile(REF)
presentation = ref.read("mathcad/settings/presentation.xml").decode("utf-8-sig")
margin = f"{MARGIN_L:.10g},{MARGIN_T:.10g},{MARGIN_R:.10g},{MARGIN_B:.10g}"
presentation = re.sub(r"<pageModel [^>]*/>",
                      f'<pageModel paper-code="A4" grid-size="Fine" orientation="Portrait" margin-type="Custom" '
                      f'page-margin="{margin}" spell-check-enabled="false" />', presentation)
content_types = (
    f'{BOM}{XML_DECL}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.mathprocessingml.mathcad.main+xml" />'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />'
    '<Default Extension="XamlPackage" ContentType="application/zip" />'
    '<Default Extension="png" ContentType="image/png" />'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml" />'
    '<Override PartName="/docProps/app.xml" ContentType="application/mathcad.extended-properties+xml" />'
    '<Override PartName="/mathcad/settings/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.mathprocessingml.mathcad.settings.presentation+xml" />'
    '<Override PartName="/mathcad/settings/calculation.xml" ContentType="application/vnd.openxmlformats-officedocument.mathprocessingml.mathcad.settings.calculation+xml" />'
    '<Override PartName="/mathcad/result.xml" ContentType="application/vnd.openxmlformats-officedocument.mathprocessingml.mathcad.result+xml" />'
    '<Override PartName="/mathcad/integration.xml" ContentType="application/vnd.openxmlformats-officedocument.mathprocessingml.mathcad.integration+xml" />'
    "</Types>")
od = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
root_rels = (
    f'{BOM}{XML_DECL}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    f'<Relationship Type="{od}" Target="/mathcad/worksheet.xml" Id="{rel_id()}" />'
    f'<Relationship Type="{od}" Target="/mathcad/header.xml" Id="{rel_id()}" />'
    f'<Relationship Type="{od}" Target="/mathcad/footer.xml" Id="{rel_id()}" />'
    '<Relationship Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
    f'Target="/docProps/core.xml" Id="{rel_id()}" /></Relationships>')
core = (f'{XML_DECL}<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties">'
        '<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Rechenbericht Kompakte Kartfelge, Konzept 2</dc:title>'
        '<dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Lenhard</dc:creator>'
        '<cp:lastModifiedBy>Lenhard</cp:lastModifiedBy><cp:revision>1</cp:revision></cp:coreProperties>')
base = {
    "[Content_Types].xml": content_types.encode(),
    "_rels/.rels": root_rels.encode(),
    "docProps/app.xml": ref.read("docProps/app.xml"),
    "docProps/core.xml": core.encode(),
    "mathcad/settings/presentation.xml": (BOM + presentation).encode(),
    "mathcad/settings/calculation.xml": ref.read("mathcad/settings/calculation.xml"),
}
with open(OUT, "wb") as fh:
    fh.write(doc.package(base))
print("geschrieben:", OUT, f"(Seitenhöhe {PAGE_H:.2f} px, Inhaltsbreite {CW:.1f} px)")

import pickle  # noqa: E402  (layout snapshot for the preview renderer)
with open(OUT + ".layout.pkl", "wb") as fh:
    pickle.dump(doc, fh)
