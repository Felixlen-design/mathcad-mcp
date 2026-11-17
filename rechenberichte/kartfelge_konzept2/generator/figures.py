"""Sketches for the worksheet: half-section of wheel/hub (cover) and free-body diagram (bearing forces)."""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
INK = "#1f1f1f"
BLUE = "#1f4e9c"
GREY = "#9a9a9a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def arrow(ax, x0, y0, x1, y1, color=BLUE, lw=1.6):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color=color, lw=lw))


def dim(ax, x0, x1, y, text, color=GREY):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="<|-|>", mutation_scale=8, color=color, lw=0.8))
    ax.text((x0 + x1) / 2, y + 2.2, text, ha="center", va="bottom", color="#555555", fontsize=8)


def cover_sketch(path):
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=220)
    # tyre (schematic)
    tyre = [(5, 69), (-2, 92), (4, 116), (22, 125), (126, 125), (144, 116), (150, 92), (143, 69)]
    ax.add_patch(Polygon(tyre, closed=False, fill=False, ec=GREY, lw=1.0, ls="-"))
    # rim shell, 4 mm wall
    outer = [(5, 63), (18, 63), (60, 44.5), (100, 44.5), (130, 63), (143, 63)]
    inner = [(x, r - 4) for x, r in reversed(outer)]
    ax.add_patch(Polygon(outer + inner, closed=True, fc="#c9d3e3", ec=INK, lw=0.8))
    for x0 in (0, 143):
        ax.add_patch(Rectangle((x0, 59), 5, 10, fc="#c9d3e3", ec=INK, lw=0.8))
    # wheel disc 12 mm at x = 13..25
    ax.add_patch(Polygon([(13, 20), (25, 20), (25, 55.9), (18, 59), (13, 59)], closed=True,
                         fc="#9fb3d1", ec=INK, lw=0.8, hatch="////"))
    # hub (existing), flange and body
    ax.add_patch(Rectangle((25, 20), 6, 16.5, fc="#e6e6e6", ec=INK, lw=0.8))
    ax.add_patch(Rectangle((19, 17.5), 101, 4, fc="#e6e6e6", ec=INK, lw=0.8))
    # bearings 6003 (17x35x10)
    for xc, lab in ((24, "A"), (115, "B")):
        ax.add_patch(Rectangle((xc - 5, 8.5), 10, 9, fc="white", ec=INK, lw=0.8))
        ax.plot([xc - 5, xc + 5], [8.5, 17.5], color=INK, lw=0.5)
        ax.plot([xc - 5, xc + 5], [17.5, 8.5], color=INK, lw=0.5)
        ax.text(xc if lab == "B" else 34, 27.5 if lab == "B" else 25, f"Lager {lab}", ha="center" if lab == "B" else "left", fontsize=8)
    # stub axle d17 with collar at x=120, continuing to the kingpin
    ax.add_patch(Rectangle((8, 0), 112, 8.5, fc="#f2f2f2", ec=INK, lw=0.8))
    ax.add_patch(Rectangle((120, 0), 85, 12.5, fc="#f2f2f2", ec=INK, lw=0.8))
    # axes and reference lines
    ax.plot([-8, 215], [0, 0], color=INK, lw=0.6, ls=(0, (8, 3, 2, 3)))
    ax.plot([74, 74], [-6, 130], color=GREY, lw=0.8, ls="--")
    ax.plot([205, 205], [-12, 95], color=INK, lw=0.9, ls=(0, (8, 3, 2, 3)))
    ax.text(74, 131, "Radmitte x = 74", ha="center", va="bottom", fontsize=8)
    ax.text(203, 97, "Lenkachse\nx = 205", ha="right", va="bottom", fontsize=8)
    ax.text(163, 14.5, "Achsschenkel Ø17, Bund x = 120", ha="center", va="bottom", fontsize=8)
    ax.text(80, 50, "Felge EN AW-6082 T6", ha="left", va="bottom", fontsize=8)
    ax.text(31, 70, "Radscheibe 12 mm\nx = 13 … 25", ha="left", va="bottom", fontsize=8)
    ax.text(74, 104, "Reifen r = 125", ha="center", fontsize=8, color="#666666")
    arrow(ax, -8, -10, 20, -10, color=INK, lw=0.9)
    ax.text(22, -10, "x (zum Kart)", va="center", fontsize=8)
    dim(ax, 0, 148, -20, "Felgenbreite 148")
    ax.set_xlim(-6, 222)
    ax.set_ylim(-26, 138)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    fig.savefig(path, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def fbd(path):
    fig, ax = plt.subplots(figsize=(6.0, 3.9), dpi=220)
    xa, xb, xr, r = 24, 115, 74, 125
    ax.plot([-5, 140], [0, 0], color=GREY, lw=2.2, solid_capstyle="butt")
    for x, lab in ((xa, "Lager A"), (xb, "Lager B")):
        ax.add_patch(plt.Circle((x, 0), 3.2, fc="white", ec=INK, lw=1.0, zorder=3))
        ax.text(x, 7 if lab == "Lager A" else -14, lab, ha="center", fontsize=9, fontweight="bold")
    ax.plot([xr, xr], [0, -r], color=GREY, lw=0.9, ls="--")
    ax.plot([xr - 25, xr + 25], [-r, -r], color=GREY, lw=1.2)
    ax.text(xr + 2, -r / 2, "r = 125 mm", fontsize=8, color="#555555")
    ax.text(xr + 2, -r / 2 - 9, "Radmitte x = 74", fontsize=8, color="#555555")
    # ground forces on the wheel
    arrow(ax, xr - 38, -r + 6, xr - 1, -r + 6, color=INK)
    ax.text(xr - 40, -r + 6, "$F_{ya}$", ha="right", va="center", fontsize=10)
    arrow(ax, xr, -r - 22, xr, -r - 1, color=INK)
    ax.text(xr + 3, -r - 18, "$F_{za}$", ha="left", va="center", fontsize=10)
    # bearing forces on the wheel, curve outside (F_A acts upward = negative in the sign convention)
    arrow(ax, xa, -38, xa, -4)
    ax.text(xa - 3, -30, "$F_{A}$", ha="right", fontsize=10, color=BLUE)
    arrow(ax, xb, 34, xb, 4)
    ax.text(xb + 3, 24, "$F_{B}$", ha="left", fontsize=10, color=BLUE)
    arrow(ax, xb + 34, 0, xb + 4, 0)
    ax.text(xb + 36, 0, "$F_{axB}$", ha="left", va="center", fontsize=10, color=BLUE)
    ax.text(-6, 0, "außen", ha="right", va="center", fontsize=8, color="#555555")
    ax.text(170, -14, "Kartseite", ha="right", va="center", fontsize=8, color="#555555")
    dim(ax, xa, xr, 44, "$a_A$ = 50 mm")
    dim(ax, xr, xb, 44, "$b_B$ = 41 mm")
    dim(ax, xa, xb, 60, "$l_L$ = 91 mm")
    ax.set_xlim(-22, 170)
    ax.set_ylim(-152, 72)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    fig.savefig(path, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


if __name__ == "__main__":
    cover_sketch(f"{OUT}/schnitt.png")
    fbd(f"{OUT}/fkb.png")
