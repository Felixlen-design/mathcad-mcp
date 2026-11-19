"""Rechenbericht Kartfelge (Kräfte, Wellendurchmesser, Lager) im Stil des Rechenberichts Pneumatik-Spanner."""
import re
import sys
import zipfile

from mathexpr import (PI, Abs, Call, Cmp, Neg, Num, Op, Paren, Root, Scale, Var, V, q)
from mcdx_doc import (BASE_SIZE, BOM, CONTENT_W, MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B, PAGE_H, PAGE_TOP,
                      PAGE_W, XML_DECL, D, Doc, E, IMG, MathCell, T, X, png_size, rel_id)

OUT, REF, IMGDIR = sys.argv[1], sys.argv[2], sys.argv[3]
CW = CONTENT_W
XH, XL, XC, XR = 19.2, 38.4, 270.0, 430.0     # sub-heading, formulas, checks, right column
GAP = 4.0
doc = Doc()
YR = {"y": 0.0}                               # right-column cursor on the current page


# ------------------------------------------------------------------ helpers
def refs(node, out=None):
    out = set() if out is None else out
    if isinstance(node, Var):
        out.add(node.name)
    if isinstance(node, Call):
        out.add(node.fname)
    for attr in ("a", "b", "c", "expr"):
        child = getattr(node, attr, None)
        if child is not None and not isinstance(child, (str, int, float)):
            refs(child, out)
    for child in getattr(node, "args", []):
        refs(child, out)
    return out


def def_top(name):
    for it in doc.items:
        c = it.cell
        if isinstance(c, MathCell) and c.kind in ("define", "defeval", "fdefine") and c.name == name:
            return it.top
    return None


def lrow(*cells, gap=GAP):
    """Row in the left/middle area; never above a definition it uses (Prime evaluates top to bottom)."""
    need = None
    for _, c in cells:
        if isinstance(c, MathCell) and c.expr is not None:
            for n in refs(c.expr):
                t = def_top(n)
                if t is not None and t >= doc.page * PAGE_H and (need is None or t > need):
                    need = t
    if need is not None and need - doc.page * PAGE_H + 2 > doc.y:
        doc.y = need - doc.page * PAGE_H + 2
    doc.row(*cells, gap=gap)


def page(title, subtitle=None, key=None):
    if doc.items:
        doc.new_page()
        doc.y = 4.0
    if key:
        doc.mark(key)
    doc.row((0, T(title, CW, size=21.3333333333333, align="Center")), gap=2 if subtitle else 12)
    if subtitle:
        doc.row((0, T(subtitle, CW, size=17.3333333333333, align="Center")), gap=12)
    YR["y"] = doc.y


def rin(cell):
    """Given value in the right column."""
    doc._live_eval([(XR, cell)])
    doc.put(cell, XR, doc.page * PAGE_H + YR["y"])
    YR["y"] += cell.height() + 4


def rimg(path, width):
    pw, ph = png_size(path)
    h = width * ph / pw
    doc.put(IMG(path, width, h), CW - width, doc.page * PAGE_H + YR["y"])
    YR["y"] += h + 8


def sub(text):
    doc.skip(4)
    lrow((XH, T(text, 380, bold=True)), gap=4)


def de(name, expr, unit=None, check=None, note=None):
    """name := expr, below it name = result; optional comparison or short text to the right of the result."""
    lrow((XL, D(name, expr)), gap=1)
    cells = [(XL, E(name, unit))]
    if check is not None:
        cells.append((XC, X(check)))
    if note:
        cells.append((XC, T(note, 150)))
    lrow(*cells, gap=GAP + 2)


def ev(expr, unit=None, check=None):
    cells = [(XL, E(expr, unit))]
    if check is not None:
        cells.append((XC, X(check)))
    lrow(*cells, gap=GAP + 3)


def txt(text):
    lrow((XL, T(text, 380)), gap=2)


Z = {"N": "N", "mm": "mm", "Nm": "N*m", "s": "N/mm^2"}

# ------------------------------------------------------------------ Seite 1: Deckblatt
doc.y = 60.0
doc.row((0, T("Rechenbericht", CW, size=34.6666666666667, bold=True, align="Center")), gap=12)
doc.row((0, T("Kompakte Kartfelge", CW, size=18.6666666666667, bold=True, align="Center")), gap=12)
doc.row((0, T("Lenhard", CW, size=BASE_SIZE, align="Center")), gap=60)
pw_, ph_ = png_size(f"{IMGDIR}/schnitt.png")
doc.row(((CW - 580) / 2, IMG(f"{IMGDIR}/schnitt.png", 580, 580 * ph_ / pw_)))

# ------------------------------------------------------------------ Seite 2: Inhaltsverzeichnis
doc.new_page()
doc.y = 0.0
doc.mark("toc")
doc.row((0, T("Inhaltsverzeichnis", CW, size=BASE_SIZE * 1.3, bold=True, align="Center")))
toc_top = doc.page * PAGE_H + 340.0

# ------------------------------------------------------------------ Kräfteberechnung
page("Kräfteberechnung", "Radlasten und Seitenkräfte", "kraft")
for c in (D("m_K", q(110, "kg")), D("m_F", q(80, "kg")), D("g_E", q(9.81, "m/s^2")), D("φ_V", Num(0.43)),
          D("h_S", q(250, "mm")), D("s_V", q(1050, "mm")), D("a_y", 1.5 * V("g_E")), D("f_St", Num(3))):
    rin(c)
sub("1) Radlast geradeaus")
de("m_ges", V("m_K") + V("m_F"), "kg")
de("G_K", V("m_ges") * V("g_E"), "N")
de("F_zs", V("φ_V") * V("G_K") / 2, "N")
sub("2) Radlasten in der Kurve")
de("ΔF_z", Op("div", 1, 2) * ((V("m_ges") * V("a_y") * V("h_S")) / V("s_V")), "N")
de("F_za", V("F_zs") + V("ΔF_z"), "N")
de("F_zi", V("F_zs") - V("ΔF_z"), "N")
sub("3) Seitenkräfte")
de("F_yV", V("φ_V") * V("m_ges") * V("a_y"), "N")
de("F_ya", V("F_yV") * V("F_za") / (2 * V("F_zs")), "N")
de("F_yi", V("F_yV") * V("F_zi") / (2 * V("F_zs")), "N")
sub("4) Stoß")
de("F_zSt", V("f_St") * V("F_zs"), "N")

page("Kräfteberechnung", "Lagerkräfte")
for c in (D("r_R", q(125, "mm")), D("b_F", q(148, "mm")), D("x_A", q(24, "mm")), D("x_B", q(115, "mm"))):
    rin(c)
YR["y"] += 10
rimg(f"{IMGDIR}/fkb.png", 175.0)
sub("1) Abstände")
de("x_R", V("b_F") / 2, "mm")
de("a_A", V("x_R") - V("x_A"), "mm")
de("b_B", V("x_B") - V("x_R"), "mm")
de("l_L", V("x_B") - V("x_A"), "mm")
sub("2) Kurve, äußeres Rad")
txt([["ΣFx = 0:   Fya − FaxB = 0"], ["ΣFz = 0:   Fza + FA − FB = 0"], ["ΣMB = 0:   Fya·r − Fza·b − FA·l = 0"]])
doc.skip(6)
de("F_axB", V("F_ya"), "N")
de("F_A2", (V("F_ya") * V("r_R") - V("F_za") * V("b_B")) / V("l_L"), "N")
de("F_B2", V("F_za") + V("F_A2"), "N")
sub("3) Geradeaus")
de("F_A1", Neg(V("F_zs") * V("b_B") / V("l_L")), "N")
de("F_B1", V("F_zs") + V("F_A1"), "N")
sub("4) Kurve, inneres Rad")
de("F_axA", V("F_yi"), "N")
de("F_A3", Neg(Paren(V("F_yi") * V("r_R") + V("F_zi") * V("b_B")) / V("l_L")), "N")
de("F_B3", V("F_zi") + V("F_A3"), "N")
sub("5) Stoß")
de("F_A4", Neg(V("F_zSt") * V("b_B") / V("l_L")), "N")
de("F_B4", V("F_zSt") + V("F_A4"), "N")

# ------------------------------------------------------------------ Wellenberechnung
page("Wellenberechnung", "Achsschenkel Ø17", "welle")
for c in (D("R_m", q(1000, "N/mm^2")), D("R_e", q(750, "N/mm^2")), D("d_A", q(17, "mm")), D("x_Bu", q(120, "mm")),
          D("f_S", Num(1.5)), D("S_erf", Num(1.5)), D("K_1", Num(0.95)), D("K_2", Num(0.9)), D("β_k", Num(1.8))):
    rin(c)
de("σ_bzul", V("R_e") / V("S_erf"), "N/mm^2")
sub("1) Biegemomente")
de("M_bB", V("F_A2") * V("l_L"), "N*m")
de("M_Bu1", V("F_B1") * (V("x_Bu") - V("x_B")) - V("F_A1") * (V("x_Bu") - V("x_A")), "N*m")
de("M_Bu2", V("F_B2") * (V("x_Bu") - V("x_B")) - V("F_A2") * (V("x_Bu") - V("x_A")), "N*m")
sub("2) Vordimensionierung")
lrow((XL, D("d_erf", Root(32 * V("f_S") * V("M_bB") / (PI * V("σ_bzul")), 3))), gap=3)
lrow((XL, E("d_erf", "mm")), (XC - 60, T("Ø vorhanden: 17 mm", 160)), gap=GAP + 3)
sub("3) Biegespannung")
de("W_b", PI * V("d_A") ** 3 / 32, "mm^3")
de("σ_b", V("f_S") * V("M_bB") / V("W_b"), "N/mm^2", check=Cmp(V("σ_b"), "<", V("σ_bzul")))
sub("4) Schubspannung")
de("A_A", PI * V("d_A") ** 2 / 4, "mm^2")
de("τ_max", Op("div", 4, 3) * (V("F_A2") / V("A_A")), "N/mm^2")
de("τ_zul", 0.5 * V("σ_bzul"), "N/mm^2", check=Cmp(V("τ_max"), "<", V("τ_zul")))
sub("5) Dauerfestigkeit am Bund")
de("M_m", Abs(V("M_Bu1") + V("M_Bu2")) / 2, "N*m")
de("M_a", Abs(V("M_Bu1") - V("M_Bu2")) / 2, "N*m")
de("σ_m", V("M_m") / V("W_b"), "N/mm^2")
de("σ_a", V("M_a") / V("W_b"), "N/mm^2")
de("σ_bW", 0.5 * V("R_m"), "N/mm^2")
de("σ_GW", V("σ_bW") * V("K_1") * V("K_2") / V("β_k"), "N/mm^2")
de("σ_GA", V("σ_GW") * (1 - V("σ_m") / V("R_m")), "N/mm^2")
de("S_D", V("σ_GA") / V("σ_a"), None, check=Cmp(V("S_D"), ">", V("S_erf")))
sub("6) Erforderlicher Durchmesser dauerfest")
de("W_erf", (V("S_erf") * V("M_a") + V("σ_GW") * V("M_m") / V("R_m")) / V("σ_GW"), "mm^3")
lrow((XL, D("d_erfD", Root(32 * V("W_erf") / PI, 3))), gap=3)
lrow((XL, E("d_erfD", "mm")), (XC - 60, T("Ø vorhanden: 17 mm", 160)), gap=GAP + 3)

# ------------------------------------------------------------------ Lagerberechnung
page("Lagerberechnung", "Rillenkugellager 6003", "lager")
for c in (D("C_r", q(6.37, "kN")), D("C_0r", q(3.25, "kN")), D("f_0", Num(14)),
          D("f_a1", Num(3.45)), D("f_a2", Num(5.17)), D("e_1", Num(0.38)), D("e_2", Num(0.42)),
          D("Y_1", Num(1.15)), D("Y_2", Num(1.04)), D("q_1", Num(0.2)), D("q_2", Num(0.2)), D("q_3", Num(0.6)),
          D("v_1", q(50, "km/hr")), D("v_max", q(80, "km/hr")), D("n_G", q(24000, "1/min")),
          D("S_0erf", Num(1)), D("f_RS", Num(1.3))):
    rin(c)
sub("1) Lagerkräfte (Kurve, äußeres Rad)")
de("F_rA", Abs(V("F_A2")), "N")
de("F_rB", Abs(V("F_B2")), "N")
de("F_a", V("F_axB"), "N")
sub("2) Äquivalente dynamische Lagerbelastung")
de("P_A", V("F_rA"), "N")
de("f_aB", V("f_0") * V("F_a") / V("C_0r"))
lin = (V("f_aB") - V("f_a1")) / (V("f_a2") - V("f_a1"))
de("e_B", V("e_1") + (V("e_2") - V("e_1")) * lin)
de("Y_B", V("Y_1") + (V("Y_2") - V("Y_1")) * lin)
ev(V("F_a") / V("F_rB"), check=Cmp(V("F_a") / V("F_rB"), ">", V("e_B")))
de("P_B", 0.56 * V("F_rB") + V("Y_B") * V("F_a"), "N")
sub("3) Lebensdauer")
de("L_10A", (V("C_r") / V("P_A")) ** 3, note="Mio. Umdrehungen")
de("L_10B", (V("C_r") / V("P_B")) ** 3, note="Mio. Umdrehungen")
de("P_mA", Root(V("q_1") * V("P_A") ** 3 + V("q_2") * Abs(V("F_A3")) ** 3 + V("q_3") * Abs(V("F_A1")) ** 3, 3), "N")
de("P_mB", Root(V("q_1") * V("P_B") ** 3 + V("q_2") * Abs(V("F_B3")) ** 3 + V("q_3") * Abs(V("F_B1")) ** 3, 3), "N")
de("L_10mA", (V("C_r") / V("P_mA")) ** 3, note="Mio. Umdrehungen")
de("L_10mB", (V("C_r") / V("P_mB")) ** 3, note="Mio. Umdrehungen")
de("n_1", V("v_1") / (2 * PI * V("r_R")), "1/min")
mio = Op("pow", 10, 6)
de("L_hA", V("L_10mA") * mio / V("n_1"), "hr")
de("L_hB", V("L_10mB") * mio / V("n_1"), "hr")
de("s_A", V("L_10mA") * mio * 2 * PI * V("r_R"), "km")
de("s_B", V("L_10mB") * mio * 2 * PI * V("r_R"), "km")
sub("4) Statische Tragsicherheit")
ev(0.6 * V("F_rB") + 0.5 * V("F_a"), "N", check=Cmp(0.6 * V("F_rB") + 0.5 * V("F_a"), "<", V("F_rB")))
de("S_0A", V("C_0r") / V("F_rA"), None, check=Cmp(V("S_0A"), ">", V("S_0erf")))
de("S_0B", V("C_0r") / V("F_rB"), None, check=Cmp(V("S_0B"), ">", V("S_0erf")))
de("S_0BR", V("S_0B") / V("f_RS"), None, check=Cmp(V("S_0BR"), ">", V("S_0erf")))
sub("5) Drehzahl")
de("n_max", V("v_max") / (2 * PI * V("r_R")), "1/min", check=Cmp(V("n_max"), "<", V("n_G")))

# ------------------------------------------------------------------ Inhaltsverzeichnis
last = doc.page + 1
sections = [("Kräfteberechnung", "kraft"), ("Wellenberechnung", "welle"), ("Lagerberechnung", "lager")]
entries = [("Deckblatt", "Seite 1"), ("Inhaltsverzeichnis", "Seite 2")]
for i, (label, key) in enumerate(sections):
    a = doc.marks[key]
    b = doc.marks[sections[i + 1][1]] - 1 if i + 1 < len(sections) else last
    entries.append((label, f"Seite {a}" if a == b else f"Seite {a}-{b}"))
y = toc_top
for label, pg in entries:
    dots = max(3, int((440 - len(label) * BASE_SIZE * 0.56) / (BASE_SIZE * 0.33)))
    doc.put(T(label + "." * dots, 500), 0.0, y)
    doc.put(T(pg, 100), 500.0, y)
    y += 40

# ------------------------------------------------------------------ Kopf- und Fußzeile
doc.header.append((T("Lenhard", 150, align="Right"), 26.0, PAGE_W - MARGIN_R - 150))
doc.footer.append((T("Donnerstag, 19. November 2026", 260), 26.0, MARGIN_L))
# Prime accepts only its 8 fixed page-number templates; the German UI shows "Seite x von y"
doc.footer_page_field = ("Page_@PageNo_of_@PagesTotal", PAGE_W - MARGIN_R - 105, 26.0, 105.0)

# ------------------------------------------------------------------ Prüfung
env, results, errors = doc.evaluate()
over = doc.overlaps()
print(f"Seiten: {last}, Regionen: {len(doc.items)}, Ergebnisse: {len(results)}")
for it, val, shown in results:
    c = it.cell
    label = lin_name = c.expr.name if isinstance(c.expr, Var) else "(Ausdruck)"
    print(f"  S.{it.page + 1:2d}  {label:10s} = {shown}")
print("Fehler:", errors if errors else "keine")
print("Überlappungen:", len(over))
for a, b in over:
    print("   ", a.page + 1, round(a.top, 1), round(a.left, 1), type(a.cell).__name__, getattr(a.cell, "name", ""),
          "<->", round(b.top, 1), round(b.left, 1), type(b.cell).__name__, getattr(b.cell, "name", ""))
names = [it.cell.name for it in doc.items if isinstance(it.cell, MathCell) and it.cell.kind == "define"]
dups = {n for n in names if names.count(n) > 1}
print("Doppelt definiert:", dups or "keine")
too_low = [it for it in doc.items if (it.top % PAGE_H) + (it.cell.height() if hasattr(it.cell, "height") else 0)
           > PAGE_H - 4]
print("Über den Seitenrand:", len(too_low))
if errors or dups or over or too_low:
    sys.exit(1)

# ------------------------------------------------------------------ Basisteile aus einem Prime-12-Arbeitsblatt
ref = zipfile.ZipFile(REF)
presentation = ref.read("mathcad/settings/presentation.xml").decode("utf-8-sig")
margin = f"{MARGIN_L:.10g},{MARGIN_T:.10g},{MARGIN_R:.10g},{MARGIN_B:.10g}"
presentation = re.sub(r"<pageModel [^>]*/>",
                      f'<pageModel paper-code="A4" grid-size="Fine" orientation="Portrait" margin-type="Custom" '
                      f'page-margin="{margin}" spell-check-enabled="false" starting-page-number="1" '
                      f'total-pages-offset="0" page-background-color="#FFF6FAF6" />', presentation)
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
core = (f'{XML_DECL}\n<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties">'
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
import pickle  # noqa: E402
with open(OUT + ".layout.pkl", "wb") as fh:
    pickle.dump(doc, fh)
print("geschrieben:", OUT)
