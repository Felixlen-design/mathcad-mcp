"""Structural checks of the generated .mcdx: XSD validation, XML well-formedness, relationships, XAML packages."""
import io
import re
import sys
import zipfile

from lxml import etree

XSD = sys.argv[2]
path = sys.argv[1]
z = zipfile.ZipFile(path)
names = set(z.namelist())
problems = []

# 1) every XML part well-formed
for n in names:
    if n.endswith((".xml", ".rels")):
        try:
            etree.fromstring(z.read(n))
        except etree.XMLSyntaxError as e:
            problems.append(f"{n}: {e}")

# 2) XSD validation (worksheet, header, footer; math regions individually; results; presentation)
ws_schema = etree.XMLSchema(etree.parse(f"{XSD}/worksheet50.xsd"))
math_schema = etree.XMLSchema(etree.parse(f"{XSD}/math50.xsd"))
for part in ("mathcad/worksheet.xml", "mathcad/header.xml", "mathcad/footer.xml"):
    doc = etree.fromstring(z.read(part))
    if not ws_schema.validate(doc):
        problems += [f"{part}: {e.message} (Zeile {e.line})" for e in ws_schema.error_log][:15]
    for tag in ("define", "eval", "apply"):
        for el in doc.iter(f"{{http://schemas.mathsoft.com/math50}}{tag}"):
            if not math_schema.validate(el):
                problems += [f"{part} ml:{tag}: {e.message}" for e in math_schema.error_log][:5]
for part, xsd in (("mathcad/result.xml", "result10.xsd"), ("mathcad/settings/presentation.xml", "presentation10.xsd")):
    sch = etree.XMLSchema(etree.parse(f"{XSD}/{xsd}"))
    if not sch.validate(etree.fromstring(z.read(part))):
        problems += [f"{part}: {e.message}" for e in sch.error_log][:10]

# 3) relationships: every item-idref resolves, every target exists
for part in ("worksheet", "header", "footer"):
    rels = etree.fromstring(z.read(f"mathcad/_rels/{part}.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    xml = z.read(f"mathcad/{part}.xml").decode()
    refs = re.findall(r'item-idref="([^"]+)"', xml)
    for ref in refs:
        if ref not in rmap:
            problems.append(f"{part}: item-idref {ref} ohne Relationship")
    for rid, tgt in rmap.items():
        if tgt.lstrip("/") not in names:
            problems.append(f"{part}: Ziel fehlt {tgt}")
    if set(rmap) - set(refs):
        problems.append(f"{part}: ungenutzte Relationships {len(set(rmap) - set(refs))}")
for r in etree.fromstring(z.read("_rels/.rels")):
    if r.get("Target").lstrip("/") not in names:
        problems.append(f"_rels/.rels: Ziel fehlt {r.get('Target')}")

# 4) XAML packages: nested zip with the three parts, BOM on content types/rels, parseable XAML
n_xaml = 0
for n in names:
    if n.endswith(".XamlPackage"):
        n_xaml += 1
        inner = zipfile.ZipFile(io.BytesIO(z.read(n)))
        if set(inner.namelist()) != {"[Content_Types].xml", "_rels/.rels", "Xaml/Document.xaml"}:
            problems.append(f"{n}: Inhalt {inner.namelist()}")
        for p in ("[Content_Types].xml", "_rels/.rels"):
            if not inner.read(p).startswith(b"\xef\xbb\xbf"):
                problems.append(f"{n}/{p}: kein BOM")
        etree.fromstring(inner.read("Xaml/Document.xaml"))

# 5) ids unique, resultRefs unique
ws = z.read("mathcad/worksheet.xml").decode() + z.read("mathcad/header.xml").decode() + z.read("mathcad/footer.xml").decode()
rid = re.findall(r'region-id="(\d+)"', ws)
if len(rid) != len(set(rid)):
    problems.append("region-id doppelt")
rr = re.findall(r'resultRef="(\d+)"', ws)
if len(rr) != len(set(rr)):
    problems.append("resultRef doppelt")
print(f"Teile: {len(names)}, XAML-Pakete: {n_xaml}, Regionen: {len(rid)}, Rechenregionen: {len(rr)}")
print("Probleme:" if problems else "Keine Probleme gefunden.")
for p in problems[:40]:
    print("  -", p)
