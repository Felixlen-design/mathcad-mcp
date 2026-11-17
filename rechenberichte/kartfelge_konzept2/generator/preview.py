"""Approximate page preview of the generated layout (not Mathcad's rendering): checks page composition."""
import pickle
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import mathexpr as mx
from mcdx_doc import CONTENT_W, PAGE_H, ImageCell, MathCell, TextCell

SYM = {"plus": " + ", "minus": " − ", "mult": "·", "div": "/", "pow": "^"}


def sub(name):
    return name.replace("_", "", 1) if "_" in name else name


def lin(n):
    if isinstance(n, mx.Num): return mx.fmt_real(n.v)
    if isinstance(n, mx.Str): return f'"{n.s}"'
    if isinstance(n, mx.Var): return sub(n.name)
    if isinstance(n, mx.Const): return n.name
    if isinstance(n, mx.Unit): return n.name
    if isinstance(n, mx.UOp): return lin(n.a) + SYM[n.kind].strip() + lin(n.b)
    if isinstance(n, mx.Scale): return f"{lin(n.num)} {lin(n.unit)}"
    if isinstance(n, mx.Paren): return f"({lin(n.a)})"
    if isinstance(n, mx.Op):
        a, b = n._kids()
        la, lb = lin(a), lin(b)
        if n.kind == "div":
            la = f"({la})" if isinstance(a, mx.Op) and a.kind != "pow" else la
            lb = f"({lb})" if isinstance(b, mx.Op) and b.kind != "pow" else lb
        return la + SYM[n.kind] + lb
    if isinstance(n, mx.Neg): return "−" + lin(n._kid())
    if isinstance(n, mx.Abs): return f"|{lin(n.a)}|"
    if isinstance(n, mx.Root): return ("∛" if n.n == 3 else "√") + f"({lin(n.a)})"
    if isinstance(n, mx.Cmp): return f"{lin(n.a)} {mx.CMP_SYM[n.op]} {lin(n.b)}"
    if isinstance(n, mx.If): return f"if({lin(n.c)}, {lin(n.a)}, {lin(n.b)})"
    if isinstance(n, mx.Call): return sub(n.fname) + "(" + ", ".join(lin(a) for a in n.args) + ")"
    return "?"


def math_text(c):
    unit = (" " + c.unit.replace("*", "·")) if c.unit else ""
    res = f" = {getattr(c, 'shown', '?')}{unit}"
    if c.kind == "define": return f"{sub(c.name)} := {lin(c.expr)}"
    if c.kind == "fdefine": return f"{sub(c.name)}({', '.join(sub(p) for p in c.params)}) := {lin(c.expr)}"
    if c.kind == "eval": return lin(c.expr) + res
    if c.kind == "defeval": return f"{sub(c.name)} := {lin(c.expr)}" + res
    return lin(c.expr)


doc = pickle.load(open(sys.argv[1], "rb"))
out = sys.argv[2]
pages = sorted({it.page for it in doc.items} | {int(it.top // PAGE_H) for it in doc.items})
for p in pages:
    fig = plt.figure(figsize=(CONTENT_W / 96 * 1.0, PAGE_H / 96 * 1.0), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, CONTENT_W); ax.set_ylim(PAGE_H, 0); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), CONTENT_W, PAGE_H, fill=False, ec="#bbbbbb", lw=0.5))
    for it in doc.items:
        if int((it.top + 1) // PAGE_H) != p:
            continue
        y = it.top - p * PAGE_H
        c = it.cell
        if isinstance(c, TextCell):
            ax.add_patch(Rectangle((it.left, y), c.width, c.height(), fill=False, ec="#e0e0ff", lw=0.4))
            txt = "\n".join("".join(r.text for r in para) for para in c.paras)
            import textwrap
            per = max(10, int(c.width / (c.size * 0.53)))
            wrapped = "\n".join(textwrap.fill(line, per) for line in txt.split("\n"))
            r0 = c.paras[0][0]
            ha = {"Left": "left", "Center": "center", "Right": "right"}[c.align]
            x = it.left + {"left": 0, "center": c.width / 2, "right": c.width}[ha]
            ax.text(x, y, wrapped, va="top", ha=ha, fontsize=c.size * 0.68, family="DejaVu Sans",
                    fontweight="bold" if r0.bold else "normal", style="italic" if r0.italic else "normal",
                    linespacing=1.15)
        elif isinstance(c, MathCell):
            ax.add_patch(Rectangle((it.left, y), c.width(), c.height(), fc="#fff6e0", ec="#e8c070", lw=0.4))
            ax.text(it.left + 2, y + c.ascent(), math_text(c), va="baseline", fontsize=8.2, family="DejaVu Serif")
        elif isinstance(c, ImageCell):
            img = plt.imread(c.path)
            ax.imshow(img, extent=(it.left, it.left + c.width, y + c.h, y))
    fig.savefig(f"{out}/page{p + 1:02d}.png")
    plt.close(fig)
print("pages:", len(pages))
