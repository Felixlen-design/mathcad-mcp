"""Small expression model for Mathcad Prime math regions.

Every node can (1) write itself as Prime math50 XML, (2) evaluate itself with units
(SI value + dimension vector) so the worksheet can be checked without Mathcad, and
(3) estimate its rendered size for the page layout.
"""
from __future__ import annotations

import math
from fractions import Fraction
from xml.sax.saxutils import escape

WPF_NS = "http://schemas.microsoft.com/winfx/2006/xaml/presentation"
PW_NS = "clr-namespace:Ptc.Wpf;assembly=Ptc.Core"

# ------------------------------------------------------------------ units
# dimension vector: (length, mass, time)
L_, M_, T_ = (1, 0, 0), (0, 1, 0), (0, 0, 1)
FORCE = (1, 1, -2)
UNITS = {
    "mm": (1e-3, L_), "cm": (1e-2, L_), "m": (1.0, L_), "km": (1e3, L_),
    "kg": (1.0, M_),
    "s": (1.0, T_), "min": (60.0, T_), "hr": (3600.0, T_),
    "N": (1.0, FORCE), "kN": (1e3, FORCE),
    "deg": (math.pi / 180, (0, 0, 0)),
}


def _dims(t):
    return tuple(Fraction(x) for x in t)


class Qty:
    """SI value with dimensions (or a string for Mathcad string results)."""

    def __init__(self, v, d=(0, 0, 0)):
        self.v = v
        self.d = _dims(d)

    @property
    def dimensionless(self):
        return all(x == 0 for x in self.d)

    def __repr__(self):
        return f"Qty({self.v}, {tuple(str(x) for x in self.d)})"


def _same(a, b, what):
    if a.d != b.d:
        raise ValueError(f"Einheitenfehler bei {what}: {a.d} vs {b.d}")


# ------------------------------------------------------------------ helpers
def ident_xml(name: str, label="VARIABLE", contextual=True, unit_override=False) -> str:
    """<ml:id>; 'F_zSt' becomes F with literal subscript zSt (Prime stores it as a WPF Span)."""
    ctx = ' label-is-contextual="true"' if contextual else ""
    if "_" in name and label == "VARIABLE":
        base, sub = name.split("_", 1)
        inner = (f'<Span xmlns="{WPF_NS}" xmlns:pw="{PW_NS}">{escape(base)}'
                 f'<pw:Subscript>{escape(sub)}</pw:Subscript></Span>')
    else:
        inner = escape(name)
    return f'<ml:id labels="{label}"{ctx} xml:space="preserve">{inner}</ml:id>'


def fmt_real(v: float) -> str:
    if float(v).is_integer():
        return str(int(v))
    s = f"{v:.12g}"
    if "e" in s:
        s = f"{v:.12f}".rstrip("0")
    return s


def name_width(name: str) -> float:
    if "_" in name:
        base, sub = name.split("_", 1)
        return 8.6 * len(base) + 6.4 * len(sub) + 2
    return 8.6 * len(name)


LINE_ASC, LINE_DESC = 15.0, 6.5   # one text line of 11 pt math


class Node:
    prec = 10

    # --- operator sugar
    def __add__(self, o): return Op("plus", self, wrap(o))
    def __radd__(self, o): return Op("plus", wrap(o), self)
    def __sub__(self, o): return Op("minus", self, wrap(o))
    def __rsub__(self, o): return Op("minus", wrap(o), self)
    def __mul__(self, o): return Op("mult", self, wrap(o))
    def __rmul__(self, o): return Op("mult", wrap(o), self)
    def __truediv__(self, o): return Op("div", self, wrap(o))
    def __rtruediv__(self, o): return Op("div", wrap(o), self)
    def __pow__(self, o): return Op("pow", self, wrap(o))
    def __neg__(self): return Neg(self)

    # --- interface
    def xml(self) -> str: raise NotImplementedError
    def ev(self, env) -> Qty: raise NotImplementedError
    def size(self):  # (width, ascent, descent)
        raise NotImplementedError


def wrap(o):
    if isinstance(o, Node):
        return o
    if isinstance(o, (int, float)):
        return Num(o)
    raise TypeError(o)


class Num(Node):
    def __init__(self, v): self.v = v
    def xml(self): return f"<ml:real>{fmt_real(self.v)}</ml:real>"
    def ev(self, env): return Qty(float(self.v))
    def size(self): return (7.6 * len(fmt_real(self.v)) + 1, LINE_ASC, LINE_DESC)


class Str(Node):
    def __init__(self, s): self.s = s
    def xml(self): return f'<ml:str xml:space="preserve">{escape(self.s)}</ml:str>'
    def ev(self, env): return Qty(self.s)
    def size(self): return (7.8 * (len(self.s) + 2), LINE_ASC, LINE_DESC)


class Var(Node):
    def __init__(self, name): self.name = name
    def xml(self): return ident_xml(self.name)
    def ev(self, env):
        if self.name not in env:
            raise NameError(f"'{self.name}' ist an dieser Stelle noch nicht definiert")
        val = env[self.name]
        if isinstance(val, Func):
            raise TypeError(f"Funktion {self.name} ohne Argumente verwendet")
        return val
    def size(self): return (name_width(self.name), LINE_ASC, LINE_DESC)


class Const(Node):
    """Built-in constant (π)."""
    def __init__(self, name, value): self.name, self.value = name, value
    def xml(self): return f'<ml:id labels="CONSTANT" label-is-contextual="true" xml:space="preserve">{self.name}</ml:id>'
    def ev(self, env): return Qty(self.value)
    def size(self): return (9.0, LINE_ASC, LINE_DESC)


PI = Const("π", math.pi)


class Unit(Node):
    def __init__(self, name):
        if name not in UNITS:
            raise KeyError(name)
        self.name = name
    def xml(self, override=False):
        if override:
            return f'<ml:id labels="UNIT" xml:space="preserve">{self.name}</ml:id>'
        return f'<ml:id labels="UNIT" label-is-contextual="true" xml:space="preserve">{self.name}</ml:id>'
    def ev(self, env):
        f, d = UNITS[self.name]
        return Qty(f, d)
    def size(self): return (9.2 * len(self.name) + 1, LINE_ASC, LINE_DESC)


def parse_unit(text: str) -> Node:
    """'N/mm^2', 'N*m', 'm/s^2', '1/min', 'km/hr', 'mm^3' -> unit expression tree."""
    text = text.replace(" ", "")
    if "/" in text:
        num, den = text.split("/", 1)
        return UOp("div", parse_unit(num), parse_unit(den))
    if "*" in text:
        a, b = text.split("*", 1)
        return UOp("mult", parse_unit(a), parse_unit(b))
    if "^" in text:
        base, exp = text.split("^")
        return UOp("pow", Unit(base), Num(int(exp)))
    if text == "1":
        return Num(1)
    return Unit(text)


class UOp(Node):
    """Operator inside a unit expression (no parentheses logic needed)."""
    def __init__(self, kind, a, b): self.kind, self.a, self.b = kind, a, b
    def xml(self, override=False):
        def x(n): return n.xml(override) if isinstance(n, (Unit, UOp)) else n.xml()
        return f"<ml:apply><ml:{self.kind} />{x(self.a)}{x(self.b)}</ml:apply>"
    def ev(self, env): return Op(self.kind, self.a, self.b).ev(env)
    def size(self): return Op(self.kind, self.a, self.b).size()


class Scale(Node):
    """Number times unit, e.g. 12 mm."""
    def __init__(self, value, unit: str):
        self.num, self.unit = wrap(value), parse_unit(unit)
    def xml(self): return f"<ml:apply><ml:scale />{self.num.xml()}{self.unit.xml()}</ml:apply>"
    def ev(self, env):
        a, u = self.num.ev(env), self.unit.ev(env)
        return Qty(a.v * u.v, u.d)
    def size(self):
        w1, a1, d1 = self.num.size(); w2, a2, d2 = self.unit.size()
        return (w1 + 5 + w2, max(a1, a2), max(d1, d2))


def q(value, unit):
    return Scale(value, unit)


class Paren(Node):
    def __init__(self, a): self.a = a
    def xml(self): return f"<ml:parens>{self.a.xml()}</ml:parens>"
    def ev(self, env): return self.a.ev(env)
    def size(self):
        w, a, d = self.a.size(); return (w + 12, a + 1, d + 1)


def _needs_paren(child: Node, parent_kind: str, side: str) -> bool:
    if isinstance(child, Scale):
        return parent_kind == "pow" and side == "left"
    if isinstance(child, (Paren, Num, Var, Unit, Const, Call, Abs, Root, Str)):
        return isinstance(child, Num) and child.v < 0 and parent_kind in ("mult", "pow", "minus", "plus") and side != "left"
    if isinstance(child, Neg):
        return parent_kind in ("mult", "pow") or (parent_kind in ("plus", "minus") and side == "right")
    if isinstance(child, Op):
        k = child.kind
        if parent_kind == "div":
            return False
        if parent_kind == "pow":
            return side == "left"
        if parent_kind == "mult":
            return k in ("plus", "minus")
        if parent_kind == "minus":
            return side == "right" and k in ("plus", "minus")
        return False
    if isinstance(child, (Cmp, If)):
        return True
    return False


class Op(Node):
    def __init__(self, kind, a, b): self.kind, self.a, self.b = kind, wrap(a), wrap(b)

    def _kids(self):
        a = Paren(self.a) if _needs_paren(self.a, self.kind, "left") else self.a
        b = Paren(self.b) if _needs_paren(self.b, self.kind, "right") else self.b
        return a, b

    def xml(self):
        a, b = self._kids()
        return f"<ml:apply><ml:{self.kind} />{a.xml()}{b.xml()}</ml:apply>"

    def ev(self, env):
        a, b = self.a.ev(env), self.b.ev(env)
        k = self.kind
        if k == "plus":
            _same(a, b, "+"); return Qty(a.v + b.v, a.d)
        if k == "minus":
            _same(a, b, "-"); return Qty(a.v - b.v, a.d)
        if k == "mult":
            return Qty(a.v * b.v, tuple(x + y for x, y in zip(a.d, b.d)))
        if k == "div":
            return Qty(a.v / b.v, tuple(x - y for x, y in zip(a.d, b.d)))
        if k == "pow":
            if not b.dimensionless:
                raise ValueError("Exponent mit Einheit")
            e = Fraction(b.v).limit_denominator(12)
            return Qty(a.v ** b.v, tuple(x * e for x in a.d))
        raise ValueError(k)

    def size(self):
        a, b = self._kids()
        wa, aa, da = a.size(); wb, ab, db = b.size()
        if self.kind == "div":
            ha, hb = aa + da, ab + db
            return (max(wa, wb) + 8, 5 + 3 + ha, hb + 3 - 5)
        if self.kind == "pow":
            return (wa + 0.72 * wb + 2, max(aa, 8 + 0.72 * (ab + db)), da)
        op_w = 9 if self.kind == "mult" else 17
        return (wa + op_w + wb, max(aa, ab), max(da, db))


class Neg(Node):
    def __init__(self, a): self.a = wrap(a)
    def _kid(self):
        return Paren(self.a) if isinstance(self.a, Op) and self.a.kind in ("plus", "minus") else self.a
    def xml(self): return f"<ml:apply><ml:neg />{self._kid().xml()}</ml:apply>"
    def ev(self, env):
        a = self.a.ev(env); return Qty(-a.v, a.d)
    def size(self):
        w, a, d = self._kid().size(); return (w + 11, a, d)


class Abs(Node):
    def __init__(self, a): self.a = wrap(a)
    def xml(self): return f"<ml:apply><ml:absval />{self.a.xml()}</ml:apply>"
    def ev(self, env):
        a = self.a.ev(env); return Qty(abs(a.v), a.d)
    def size(self):
        w, a, d = self.a.size(); return (w + 8, a + 1, d + 1)


class Root(Node):
    """n-th root; n=None is the square root."""
    def __init__(self, a, n=None): self.a, self.n = wrap(a), n
    def xml(self):
        idx = "<ml:placeholder />" if self.n is None else Num(self.n).xml()
        return f"<ml:apply><ml:nthRoot />{idx}{self.a.xml()}</ml:apply>"
    def ev(self, env):
        a = self.a.ev(env); n = 2 if self.n is None else self.n
        return Qty(a.v ** (1.0 / n), tuple(x / n for x in a.d))
    def size(self):
        w, a, d = self.a.size(); return (w + 20, a + 4, d + 1)


CMP = {"<": "lessThan", "<=": "lessOrEqual", ">": "greaterThan", ">=": "greaterOrEqual"}
CMP_SYM = {"<": "<", "<=": "≤", ">": ">", ">=": "≥"}


class Cmp(Node):
    def __init__(self, a, op, b): self.a, self.op, self.b = wrap(a), op, wrap(b)
    def xml(self): return f"<ml:apply><ml:{CMP[self.op]} />{self.a.xml()}{self.b.xml()}</ml:apply>"
    def ev(self, env):
        a, b = self.a.ev(env), self.b.ev(env); _same(a, b, self.op)
        r = {"<": a.v < b.v, "<=": a.v <= b.v, ">": a.v > b.v, ">=": a.v >= b.v}[self.op]
        return Qty(1.0 if r else 0.0)
    def size(self):
        wa, aa, da = self.a.size(); wb, ab, db = self.b.size()
        return (wa + wb + 20, max(aa, ab), max(da, db))


class If(Node):
    """Inline if(cond, a, b) - stored by Prime as KEYWORD if + sequence."""
    def __init__(self, c, a, b): self.c, self.a, self.b = c, wrap(a), wrap(b)
    def xml(self):
        return ('<ml:apply><ml:id labels="KEYWORD" xml:space="preserve">if</ml:id><ml:sequence>'
                f"{self.c.xml()}{self.a.xml()}{self.b.xml()}</ml:sequence></ml:apply>")
    def ev(self, env):
        return self.a.ev(env) if self.c.ev(env).v else self.b.ev(env)
    def size(self):
        parts = [self.c.size(), self.a.size(), self.b.size()]
        return (sum(p[0] for p in parts) + 40, max(p[1] for p in parts), max(p[2] for p in parts))


class Func:
    """A user function value in the evaluation environment (captures definitions above it)."""
    def __init__(self, params, body, env):
        self.params, self.body, self.env = params, body, dict(env)


class Call(Node):
    def __init__(self, fname, *args): self.fname, self.args = fname, [wrap(a) for a in args]
    def xml(self):
        head = ident_xml(self.fname)
        if len(self.args) == 1:
            return f"<ml:apply>{head}{self.args[0].xml()}</ml:apply>"
        inner = "".join(a.xml() for a in self.args)
        return f"<ml:apply>{head}<ml:sequence>{inner}</ml:sequence></ml:apply>"
    def ev(self, env):
        f = env.get(self.fname)
        if not isinstance(f, Func):
            raise NameError(f"Funktion '{self.fname}' ist hier nicht definiert")
        if len(f.params) != len(self.args):
            raise TypeError(f"{self.fname}: falsche Argumentanzahl")
        local = dict(f.env)
        for p, a in zip(f.params, self.args):
            local[p] = a.ev(env)
        return f.body.ev(local)
    def size(self):
        parts = [a.size() for a in self.args]
        w = name_width(self.fname) + 14 + sum(p[0] for p in parts) + 9 * (len(parts) - 1)
        return (w, max(p[1] for p in parts), max(p[2] for p in parts))


def V(name): return Var(name)
def F(name, *args): return Call(name, *args)
