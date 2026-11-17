"""Page layout, unit-checked evaluation and .mcdx packaging for a Mathcad Prime worksheet.

XML shapes follow worksheets saved by Mathcad Prime 11/12 (worksheet50 / math50 namespaces).
"""
from __future__ import annotations

import io
import math
import secrets
import struct
import zipfile
from dataclasses import dataclass, field
from xml.sax.saxutils import escape, quoteattr

from mathexpr import (LINE_ASC, LINE_DESC, Func, Node, Qty, Var, ident_xml, name_width,
                      parse_unit)

# ------------------------------------------------------------------ page geometry (px, 96 dpi)
MM = 96 / 25.4
PAGE_W = 210 * MM
MARGIN_L = MARGIN_T = MARGIN_R = MARGIN_B = 23.5 * MM   # equal margins: page-margin order cannot matter
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R          # 604.7 px
PAGE_H = 297 * MM - MARGIN_T - MARGIN_B           # 250 mm = 944.88 px usable height per page
PAGE_TOP = 9.6                                    # first row below a page break
BOTTOM_RESERVE = 28.0                             # keep free at the bottom of each page
ROW_GAP = 4.0

TEXT_FONT = "Tahoma"
BASE_SIZE = 14.6666666666667                      # 11 pt, Prime's "Normal" style
WS_NS = "http://schemas.mathsoft.com/worksheet50"
ML_NS = "http://schemas.mathsoft.com/math50"
WPF_NS = "http://schemas.microsoft.com/winfx/2006/xaml/presentation"
REL_FLOW = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/flowDocument"
REL_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
XML_DECL = '<?xml version="1.0" encoding="utf-8"?>'
BOM = "﻿"

SECTION_ATTRS = (
    'xml:space="preserve" TextAlignment="{align}" LineHeight="Auto" IsHyphenationEnabled="False" '
    'xml:lang="de-de" FlowDirection="LeftToRight" NumberSubstitution.CultureSource="Text" '
    'NumberSubstitution.Substitution="AsCulture" FontFamily="Tahoma" FontStyle="Normal" FontWeight="Normal" '
    'FontStretch="Normal" FontSize="{size}" Foreground="#FF000000" Typography.StandardLigatures="True" '
    'Typography.ContextualLigatures="True" Typography.DiscretionaryLigatures="False" '
    'Typography.HistoricalLigatures="False" Typography.AnnotationAlternates="0" '
    'Typography.ContextualAlternates="True" Typography.HistoricalForms="False" Typography.Kerning="True" '
    'Typography.CapitalSpacing="False" Typography.CaseSensitiveForms="False" '
    + " ".join(f'Typography.StylisticSet{i}="False"' for i in range(1, 21)) +
    ' Typography.Fraction="Normal" Typography.SlashedZero="False" Typography.MathematicalGreek="False" '
    'Typography.EastAsianExpertForms="False" Typography.Variants="Normal" Typography.Capitals="Normal" '
    'Typography.NumeralStyle="Normal" Typography.NumeralAlignment="Normal" Typography.EastAsianWidths="Normal" '
    'Typography.EastAsianLanguage="Normal" Typography.StandardSwashes="0" Typography.ContextualSwashes="0" '
    'Typography.StylisticAlternates="0"'
)


def rel_id() -> str:
    return "R" + secrets.token_hex(8)


def fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


# ------------------------------------------------------------------ cell specs
@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    size: float | None = None
    underline: bool = False


def _paragraphs(text):
    """str | Run | [str|Run] (one paragraph) | [[...], [...]] (several) -> list of list of Run."""
    if isinstance(text, (str, Run)):
        text = [[text]]
    elif text and not isinstance(text[0], list):
        text = [text]
    return [[Run(r) if isinstance(r, str) else r for r in p] for p in text]


class TextCell:
    def __init__(self, text, width, size=BASE_SIZE, bold=False, align="Left", italic=False):
        self.paras = _paragraphs(text)
        for p in self.paras:
            for r in p:
                r.bold = r.bold or bold
                r.italic = r.italic or italic
                r.size = r.size or size
        self.width, self.size, self.align = width, size, align

    def height(self):
        lines = 0.0
        for p in self.paras:
            w = 0.0
            for r in p:
                factor = 0.60 if r.bold else 0.545
                dots = r.text.count(".")
                w += ((len(r.text) - dots) * factor + dots * 0.3) * r.size
            lines += max(1, math.ceil(w / (self.width - 4)))
        big = max(r.size for p in self.paras for r in p)
        return lines * big * 1.215 + 2

    def ascent(self):
        return max(r.size for r in self.paras[0]) * 0.98

    def xaml(self) -> str:
        out = [f'<Section xmlns="{WPF_NS}" ' + SECTION_ATTRS.format(align=self.align, size=self.size) + ">"]
        for p in self.paras:
            out.append(f'<Paragraph TextAlignment="{self.align}">')
            for r in p:
                attrs = ' style="Normal"'
                if r.bold:
                    attrs += ' FontWeight="Bold"'
                if r.italic:
                    attrs += ' FontStyle="Italic"'
                if r.size and abs(r.size - self.size) > 1e-6:
                    attrs += f' FontSize="{r.size}"'
                if r.underline:
                    attrs += ' TextDecorations="Underline"'
                out.append(f"<Run{attrs}>{escape(r.text)}</Run>")
            out.append("</Paragraph>")
        out.append("</Section>")
        return "".join(out)


class MathCell:
    """kind: define | fdefine | eval | defeval | expr"""

    def __init__(self, kind, name=None, expr: Node | None = None, unit=None, prec=None, params=None):
        self.kind, self.name, self.expr, self.unit, self.prec, self.params = kind, name, expr, unit, prec, params

    # ---- xml
    def _override(self):
        if self.unit:
            u = parse_unit(self.unit)
            return u.xml(override=True) if hasattr(u, "xml") else u.xml()
        return "<ml:placeholder />"

    def _eval_xml(self):
        return f"<ml:eval>{self.expr.xml()}<ml:unitOverride>{self._override()}</ml:unitOverride></ml:eval>"

    def body(self) -> str:
        k = self.kind
        if k == "define":
            return f"<ml:define>{ident_xml(self.name, contextual=False)}{self.expr.xml()}</ml:define>"
        if k == "fdefine":
            bv = "".join(ident_xml(p, contextual=False) for p in self.params)
            return (f"<ml:define><ml:function>{ident_xml(self.name, contextual=False)}<ml:boundVars>{bv}"
                    f"</ml:boundVars></ml:function>{self.expr.xml()}</ml:define>")
        if k == "eval":
            return self._eval_xml()
        if k == "defeval":
            return f"<ml:define>{ident_xml(self.name, contextual=False)}{self._eval_xml()}</ml:define>"
        if k == "expr":
            return self.expr.xml()
        raise ValueError(k)

    def result_format(self) -> str:
        if self.prec is None:
            return ""
        return (f'<resultFormat><decimal precision="{self.prec}" show-trailing-zeros="false" radix="dec" '
                f'imaginary-value="i" /></resultFormat>')

    # ---- size
    def _size(self):
        w, a, d = self.expr.size()
        if self.kind in ("define", "defeval"):
            w += name_width(self.name) + 24
        if self.kind == "fdefine":
            w += name_width(self.name) + 24 + sum(name_width(p) + 9 for p in self.params) + 12
        if self.kind in ("eval", "defeval"):
            unit_w = 0 if not self.unit else 9.2 * len(self.unit.replace("*", "").replace("^", "")) + 6
            shown = getattr(self, "shown", None)
            w += 18 + (7.8 * len(shown) + 4 if shown else 8 * 9) + unit_w
            if self.unit and "/" in self.unit:
                a, d = max(a, 21), max(d, 15)
        return w, a + 2, d + 2

    def width(self):
        return self._size()[0]

    def height(self):
        _, a, d = self._size()
        return max(a + d, 21.0)

    def ascent(self):
        return self._size()[1]


class ImageCell:
    def __init__(self, png_path, width, height):
        self.path, self.width, self.h = png_path, width, height

    def height(self):
        return self.h

    def ascent(self):
        return 0.0


# convenience constructors
def D(name, expr): return MathCell("define", name, expr)
def DF(name, params, expr): return MathCell("fdefine", name, expr, params=params)
def E(expr, unit=None, prec=None):
    if isinstance(expr, str):
        expr = Var(expr)
    return MathCell("eval", expr=expr, unit=unit, prec=prec)
def DE(name, expr, unit=None, prec=None): return MathCell("defeval", name, expr, unit, prec)
def X(expr): return MathCell("expr", expr=expr)
def T(text, width=CONTENT_W, size=BASE_SIZE, bold=False, align="Left", italic=False):
    return TextCell(text, width, size, bold, align, italic)
def IMG(path, width, height): return ImageCell(path, width, height)


# ------------------------------------------------------------------ placed items
@dataclass
class Placed:
    cell: object
    top: float      # absolute worksheet coordinate
    left: float
    page: int


@dataclass
class Doc:
    items: list = field(default_factory=list)
    breaks: list = field(default_factory=list)
    header: list = field(default_factory=list)   # TextCells placed in header (cell, top, left)
    footer: list = field(default_factory=list)
    footer_page_field: tuple | None = None
    page: int = 0
    y: float = 0.0
    marks: dict = field(default_factory=dict)
    env: dict = field(default_factory=dict)

    @property
    def abs_y(self):
        return self.page * PAGE_H + self.y

    def new_page(self):
        self.page += 1
        self.breaks.append(self.page * PAGE_H)
        self.y = PAGE_TOP

    def ensure(self, h):
        if self.y + h > PAGE_H - BOTTOM_RESERVE and self.y > PAGE_TOP + 1:
            self.new_page()

    def skip(self, px):
        self.y += px

    def mark(self, key):
        self.marks[key] = self.page + 1

    def _live_eval(self, cells):
        """Evaluate math cells as they are placed (same order as Prime) so result widths are known."""
        for _, c in sorted(cells, key=lambda xc: xc[0]):
            if not isinstance(c, MathCell):
                continue
            try:
                if c.kind == "define":
                    self.env[c.name] = c.expr.ev(self.env)
                elif c.kind == "fdefine":
                    self.env[c.name] = Func(c.params, c.expr, self.env)
                elif c.kind in ("eval", "defeval"):
                    val = c.expr.ev(self.env)
                    if c.kind == "defeval":
                        self.env[c.name] = val
                    c.shown = mathcad_number(val, c.unit, c.prec)
            except Exception:  # noqa: BLE001 - reported by evaluate()
                pass

    def row(self, *cells, gap=ROW_GAP, keep=0.0):
        """cells: (x, cell) pairs; aligned on a common baseline. keep: extra space that must fit too."""
        self._live_eval(cells)
        base = max(c.ascent() for _, c in cells)
        offs = [base - c.ascent() for _, c in cells]
        # Prime evaluates top to bottom: a math region must never start above a math region to its left
        order = sorted(range(len(cells)), key=lambda i: cells[i][0])
        highest = None
        for i in order:
            if isinstance(cells[i][1], MathCell):
                if highest is not None and offs[i] < highest:
                    offs[i] = highest
                highest = offs[i] if highest is None else max(highest, offs[i])
        h = max(o + c.height() for o, (_, c) in zip(offs, cells))
        self.ensure(h + keep)
        for o, (x, c) in zip(offs, cells):
            self.items.append(Placed(c, self.abs_y + o, x, self.page))
        self.y += h + gap
        return h

    def put(self, cell, x, top_abs):
        """Place a cell at a fixed position (no flow)."""
        self.items.append(Placed(cell, top_abs, x, int(top_abs // PAGE_H)))

    # ---------------------------------------------------------- checks
    def overlaps(self):
        """Pairs of regions whose estimated boxes overlap (layout sanity check)."""
        boxes = []
        for it in self.items:
            c = it.cell
            w = c.width if isinstance(c, (TextCell, ImageCell)) else c.width()
            boxes.append((it.left, it.top, it.left + w, it.top + c.height(), it))
        bad = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] < b[2] - 1 and b[0] < a[2] - 1 and a[1] < b[3] - 1 and b[1] < a[3] - 1:
                    bad.append((a[4], b[4]))
        return bad

    def evaluate(self):
        """Evaluate all math regions in Prime's order (top to bottom, then left to right)."""
        env, results, errors = {}, [], []
        maths = sorted((it for it in self.items if isinstance(it.cell, MathCell)), key=lambda i: (round(i.top, 3), i.left))
        for it in maths:
            c = it.cell
            try:
                if c.kind == "define":
                    env[c.name] = c.expr.ev(env)
                elif c.kind == "fdefine":
                    env[c.name] = Func(c.params, c.expr, env)
                elif c.kind in ("eval", "defeval"):
                    val = c.expr.ev(env)
                    if c.kind == "defeval":
                        env[c.name] = val
                    results.append((it, val, display(val, c.unit)))
                elif c.kind == "expr":
                    val = c.expr.ev(env)
                    results.append((it, val, "wahr" if val.v == 1.0 else "FALSCH"))
                    if val.v != 1.0:
                        errors.append((it, "Vergleich ist falsch"))
            except Exception as exc:  # noqa: BLE001 - report every problem
                errors.append((it, str(exc)))
        return env, results, errors

    # ---------------------------------------------------------- package
    def package(self, base_parts: dict[str, bytes]) -> bytes:
        parts = dict(base_parts)
        rels_ws, rels_h, rels_f = [], [], []
        media_count = [0]
        flow_count = [0]
        region_id = [0]
        result_id = [0]

        def next_region():
            region_id[0] += 1
            return region_id[0] - 1

        def text_region(cell: TextCell, top, left, rels):
            rid = rel_id()
            part = f"mathcad/xaml/FlowDocument{flow_count[0]}.XamlPackage"
            flow_count[0] += 1
            parts[part] = xaml_package(cell.xaml())
            rels.append((rid, REL_FLOW, "/" + part))
            h = cell.height()
            return (f'<region region-id="{next_region()}" width="{fmt(cell.width)}" actualWidth="{fmt(cell.width)}" '
                    f'actualHeight="{fmt(h)}" top="{fmt(top)}" left="{fmt(left)}"><text item-idref="{rid}">'
                    f'<FlowDocument FontFamily="{TEXT_FONT}" FontStyle="Normal" FontWeight="Normal" '
                    f'FontSize="{cell.size}" Foreground="#FF000000" Background="#00FFFFFF" '
                    f'TextAlignment="{cell.align}" xml:lang="de-de" Typography.Variants="Normal" '
                    f'xmlns="{WPF_NS}" /></text></region>')

        regions = []
        for it in sorted(self.items, key=lambda i: (i.top, i.left)):
            c = it.cell
            if isinstance(c, TextCell):
                regions.append(text_region(c, it.top, it.left, rels_ws))
            elif isinstance(c, MathCell):
                rr = result_id[0]; result_id[0] += 1
                regions.append(
                    f'<region region-id="{next_region()}" actualWidth="{fmt(c.width())}" '
                    f'actualHeight="{fmt(c.height())}" top="{fmt(it.top)}" left="{fmt(it.left)}">'
                    f'<math resultRef="{rr}">{c.body()}{c.result_format()}</math></region>')
            elif isinstance(c, ImageCell):
                media_count[0] += 1
                name = f"mathcad/media/Image{media_count[0]}.png"
                with open(c.path, "rb") as fh:
                    parts[name] = fh.read()
                rid = rel_id()
                rels_ws.append((rid, REL_IMAGE, "/" + name))
                w, h = fmt(c.width), fmt(c.h)
                regions.append(
                    f'<region region-id="{next_region()}" height="{h}" width="{w}" actualWidth="{w}" '
                    f'actualHeight="{h}" top="{fmt(it.top)}" left="{fmt(it.left)}"><picture>'
                    f'<png item-idref="{rid}" display-width="{w}" display-height="{h}" /></picture></region>')
        for top in self.breaks:
            regions.append(
                f'<region region-id="{next_region()}" height="2" actualWidth="{fmt(CONTENT_W)}" actualHeight="2" '
                f'top="{fmt(top)}" left="0"><pageBreak /></region>')
        # keep document order by position
        regions.sort(key=lambda r: float(r.split(' top="')[1].split('"')[0]))

        header_regions = [text_region(c, top, left, rels_h) for c, top, left in self.header]
        footer_regions = [text_region(c, top, left, rels_f) for c, top, left in self.footer]
        if self.footer_page_field:
            template, left, top, width = self.footer_page_field
            footer_regions.append(
                f'<region region-id="{next_region()}" actualWidth="{fmt(width)}" actualHeight="17.7" top="{fmt(top)}" '
                f'left="{fmt(left)}"><fieldText><text><FlowDocument FontFamily="{TEXT_FONT}" FontStyle="Normal" '
                f'FontWeight="Normal" FontSize="{BASE_SIZE}" Foreground="#FF000000" Background="#00FFFFFF" '
                f'TextAlignment="Left" Typography.Variants="Normal" xmlns="{WPF_NS}"><Paragraph>'
                f'{escape(template.replace("_", " ").replace("@PageNo", "1").replace("@PagesTotal", "1"))}'
                f'</Paragraph></FlowDocument></text><pageNumber template={quoteattr(template)} /></fieldText></region>')

        ns = (f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
              f'xmlns:ve="http://schemas.openxmlformats.org/markup-compatibility/2006" '
              f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
              f'xmlns:ws="{WS_NS}" xmlns:ml="{ML_NS}" xmlns:u="http://schemas.mathsoft.com/units10" '
              f'xmlns:p="http://schemas.mathsoft.com/provenance10" xmlns="{WS_NS}"')
        parts["mathcad/worksheet.xml"] = (
            f'{XML_DECL}<worksheet msg-id="NoMessage" {ns}><regions>{"".join(regions)}</regions></worksheet>').encode()
        parts["mathcad/header.xml"] = f'{XML_DECL}<header {ns}><regions>{"".join(header_regions)}</regions></header>'.encode()
        parts["mathcad/footer.xml"] = f'{XML_DECL}<footer {ns}><regions>{"".join(footer_regions)}</regions></footer>'.encode()
        parts["mathcad/_rels/worksheet.xml.rels"] = rels_xml(rels_ws)
        parts["mathcad/_rels/header.xml.rels"] = rels_xml(rels_h)
        parts["mathcad/_rels/footer.xml.rels"] = rels_xml(rels_f)
        results = "".join(f'<resultData result-id="{i}" calculation-status="Pending"><ml:result /></resultData>'
                          for i in range(result_id[0]))   # Prime's own "not yet calculated" state
        parts["mathcad/result.xml"] = (
            f'{BOM}{XML_DECL}<resultsList xmlns:ml="{ML_NS}" xmlns:u="http://schemas.mathsoft.com/units10" '
            f'xmlns="http://schemas.mathsoft.com/result10">{results}</resultsList>').encode()
        parts["mathcad/integration.xml"] = (
            f'{BOM}{XML_DECL}<regions xmlns="http://schemas.ptc.com/integration10" />').encode()
        return zip_parts(parts)


# ------------------------------------------------------------------ result display
def display(val: Qty, unit: str | None) -> str:
    if isinstance(val.v, str):
        return f'"{val.v}"'
    if unit:
        u = parse_unit(unit).ev({})
        if tuple(u.d) != tuple(val.d):
            raise ValueError(f"Anzeigeeinheit {unit} passt nicht zur Dimension {tuple(str(x) for x in val.d)}")
        return f"{val.v / u.v:.6g} {unit}"
    if not val.dimensionless:
        raise ValueError(f"Ergebnis hat Einheit {tuple(str(x) for x in val.d)}, aber keine Anzeigeeinheit")
    return f"{val.v:.6g}"


def mathcad_number(val: Qty, unit, prec) -> str:
    if isinstance(val.v, str):
        return f'"{val.v}"'
    v = val.v / parse_unit(unit).ev({}).v if unit else val.v
    p = 3 if prec is None else prec
    txt = f"{v:.{p}f}"
    if "." in txt:
        txt = txt.rstrip("0").rstrip(".")
    return txt


# ------------------------------------------------------------------ packaging helpers
def rels_xml(rels) -> bytes:
    body = "".join(f'<Relationship Type="{t}" Target="{tgt}" Id="{i}" />' for i, t, tgt in rels)
    return (f'{BOM}{XML_DECL}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{body}</Relationships>").encode()


def xaml_package(document_xaml: str) -> bytes:
    ct = (f'{BOM}{XML_DECL}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="xaml" ContentType="application/vnd.ms-wpf.xaml+xml" />'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" /></Types>')
    rels = (f'{BOM}{XML_DECL}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Type="http://schemas.microsoft.com/wpf/2005/10/xaml/entry" Target="/Xaml/Document.xaml" '
            f'Id="{rel_id()}" /></Relationships>')
    return zip_parts({"Xaml/Document.xaml": document_xaml.encode(), "_rels/.rels": rels.encode(),
                      "[Content_Types].xml": ct.encode()}, content_types_first=False)


def zip_parts(parts: dict[str, bytes], content_types_first=True) -> bytes:
    names = list(parts)
    if content_types_first and "[Content_Types].xml" in names:
        names.remove("[Content_Types].xml")
        names.insert(0, "[Content_Types].xml")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, parts[n])
    return buf.getvalue()


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24])
