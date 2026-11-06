#!/usr/bin/env python3
"""Every way to cross two ropes at the 8 crossings of the hand-drawn key,
worked out again and checked against the hand-made index. The drawings and
the index are kept unchanged in scans/ and original/.

    python3 knot_crossings.py           # writes results/, index.html and turn.html
    python3 knot_crossings.py --check   # exits 1 if any of them would change

Standard library only.

  results/knots.txt    all 256 drawings: crossings circled, over and under
                       along each rope, linking number, group, name given
  results/groups.txt   the drawings grouped into knots
  results/checks.txt   the index set beside the groups
  results/closures.txt each drawing's ends joined two ways, and the links and
                       knots that makes, by Jones and Alexander polynomial
  turn.html            any drawing as two ropes in 3D (three.js), ends loose
                       or joined, plain or laid rope
"""
import functools
import math
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

# The key drawing (scan page 3), traced: where each crossing sits, and the
# path of each rope through the crossings, with points between them where the
# rope bends. Units are pixels of the key enlarged four times, y down.
CROSSINGS = {1: (175, 295), 2: (460, 300), 3: (275, 420), 4: (140, 610),
             5: (410, 665), 6: (300, 790), 7: (200, 875), 8: (415, 900)}
ROPES = [
    ("1st", [(530, 990), 8, 6, 4, (90, 450), 1, (340, 150), (450, 240), 2,
             (465, 500), 5, 6, 7, (30, 1030)]),
    ("2nd", [(75, 215), 1, 3, 5, (440, 780), 8, (330, 925), 7, (150, 830),
             (125, 700), 4, 3, (380, 330), 2, (640, 265)]),
]


def point(w):
    return CROSSINGS[w] if isinstance(w, int) else w


# Every time a rope passes a crossing, in the order the ropes are followed:
# the 1st rope from its start to its arrow, then the 2nd.
PASSES = []          # (rope, crossing, direction, position)
for r, (_, path) in enumerate(ROPES):
    for i, w in enumerate(path):
        if isinstance(w, int):
            (x0, y0), (x1, y1) = point(path[i - 1]), point(path[i + 1])
            PASSES.append((r, w, (x1 - x0, y1 - y0), point(w)))
AT = defaultdict(list)
for i, p in enumerate(PASSES):
    AT[p[1]].append(i)


def over(n, k):
    """The pass that goes over at crossing k in drawing n. The first pass goes
    over; a circle (bit k-1 of n) puts it under."""
    first, second = AT[k]
    return second if n >> (k - 1) & 1 else first


def words(n):
    """Over and under along each rope, as O and U."""
    return ["".join("O" if over(n, k) == i else "U"
                    for i, (r, k, _, _) in enumerate(PASSES) if r == rope)
            for rope in range(len(ROPES))]


def alternating(n):
    return all(a != b for w in words(n) for a, b in zip(w, w[1:]))


# Laurent polynomials in A, as {exponent: coefficient}.
def padd(p, q):
    r = dict(p)
    for k, v in q.items():
        r[k] = r.get(k, 0) + v
    return {k: v for k, v in r.items() if v}


def pmul(p, q):
    r = {}
    for a, x in p.items():
        for b, y in q.items():
            r[a + b] = r.get(a + b, 0) + x * y
    return {k: v for k, v in r.items() if v}


LOOP = {2: -1, -2: -1}           # a closed loop counts -A^2 - A^-2


def sign(n, k):
    """+1 or -1 for crossing k of drawing n, with each rope run from its start
    (y is flipped so that the plane has the usual orientation)."""
    o = over(n, k)
    u = next(i for i in AT[k] if i != o)
    (ox, oy), (ux, uy) = PASSES[o][2], PASSES[u][2]
    return 1 if ox * -uy - -oy * ux > 0 else -1


def linking(n):
    """Linking number of the two ropes once each is closed on itself."""
    s = sum(sign(n, k) for k in CROSSINGS
            if PASSES[AT[k][0]][0] != PASSES[AT[k][1]][0])
    return s // 2


def diagram(n):
    """The drawing as numbered pieces of rope between crossings. Returns each
    crossing as its four pieces counterclockwise from the one coming in
    underneath (the PD-code order), the four ends (1st start, 1st end, 2nd
    start, 2nd end), and how many pieces there are."""
    edge_in, edge_out, ends = {}, {}, []
    e = 0
    for rope in range(len(ROPES)):
        ends.append(e)
        for i, p in enumerate(PASSES):
            if p[0] == rope:
                edge_in[i], edge_out[i] = e, e + 1
                e += 1
        ends.append(e)
        e += 1
    crossings = []
    for k in CROSSINGS:
        o = over(n, k)
        u = next(i for i in AT[k] if i != o)
        (ux, uy), (ox, oy) = PASSES[u][2], PASSES[o][2]
        arms = [((-ux, uy), edge_in[u]), ((ux, -uy), edge_out[u]),
                ((-ox, oy), edge_in[o]), ((ox, -oy), edge_out[o])]
        start = math.atan2(arms[0][0][1], arms[0][0][0])
        arms.sort(key=lambda a: (math.atan2(a[0][1], a[0][0]) - start) % math.tau)
        crossings.append([edge for _, edge in arms])
    return crossings, ends, e


@functools.lru_cache(maxsize=None)
def bracket(n):
    """Kauffman bracket of the drawing as a tangle with its four ends held:
    f <ends of each rope joined> + g <ends joined across>, unnormalised."""
    crossings, ends, e = diagram(n)
    f, g = {}, {}
    for state in range(1 << len(crossings)):
        parent = list(range(e))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        a_count = 0
        for j, (a, b, c, d) in enumerate(crossings):
            if state >> j & 1:
                pairs, a_count = ((a, b), (c, d)), a_count + 1
            else:
                pairs = ((a, d), (b, c))
            for x, y in pairs:
                parent[find(x)] = find(y)
        outer = {find(x) for x in ends}
        term = {2 * a_count - len(crossings): 1}
        for _ in range(len({find(x) for x in range(e)} - outer)):
            term = pmul(term, LOOP)
        if find(ends[0]) == find(ends[1]):
            f = padd(f, term)
        else:
            g = padd(g, term)
    return f, g


# Closing the ends ---------------------------------------------------------
#
# The four ends lie on the outside of the drawing, in the order 2nd start
# (top left), 2nd end (top right), 1st start (bottom right), 1st end (bottom
# left). They can be joined without adding a crossing in two ways: each
# rope's end back to its own start, which makes two loops (a link), or each
# rope's end on to the other rope's start, which makes one loop (a knot).
# Both keep the direction the ropes are followed in, so every crossing keeps
# its sign.
CLOSURES = ("own", "across")


def writhe(n):
    return sum(sign(n, k) for k in CROSSINGS)


def jones(n, closure):
    """Jones polynomial of the closed drawing, as {4 x exponent of t: coefficient}.
    From the bracket with one loop counted 1, times (-A^3)^-writhe, A = t^(-1/4)."""
    f, g = bracket(n)
    closed = padd(pmul(f, LOOP), g) if closure == "own" else padd(f, pmul(g, LOOP))
    w = writhe(n)
    return {-a: c for a, c in pmul(closed, {-3 * w: (-1) ** (w % 2)}).items()}


def closed_crossings(n, closure):
    crossings, (s1, t1, s2, t2), _ = diagram(n)
    join = {t1: s1, t2: s2} if closure == "own" else {t1: s2, t2: s1}
    return [[join.get(x, x) for x in c] for c in crossings]


def determinant(m):
    """Determinant of a square matrix of Fractions, by elimination."""
    m = [row[:] for row in m]
    d = Fraction(1)
    for i in range(len(m)):
        p = next((r for r in range(i, len(m)) if m[r][i]), None)
        if p is None:
            return Fraction(0)
        if p != i:
            m[i], m[p], d = m[p], m[i], -d
        d *= m[i][i]
        for r in range(i + 1, len(m)):
            q = m[r][i] / m[i][i]
            for c in range(i, len(m)):
                m[r][c] -= q * m[i][c]
    return d


def alexander(n, closure):
    """Alexander polynomial of the closed drawing, as its coefficients from
    t^0 up, lowest term first and positive: a minor of the Alexander matrix of
    the Wirtinger presentation. Each entry is at most linear in t, so the minor
    is found at enough whole numbers t and the polynomial through them taken."""
    crossings = closed_crossings(n, closure)
    parent = {x: x for c in crossings for x in c}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for _, b, _, d in crossings:          # the piece going over is one arc
        parent[find(b)] = find(d)
    arcs = sorted({find(x) for x in parent})
    col = {a: i for i, a in enumerate(arcs)}

    def minor(t):
        rows = []
        for (a, b, c, _), k in zip(crossings, CROSSINGS):
            row = [Fraction(0)] * len(arcs)
            row[col[find(b)]] += 1 - t
            under_in, under_out = (t, -1) if sign(n, k) > 0 else (-1, t)
            row[col[find(a)]] += under_in
            row[col[find(c)]] += under_out
            rows.append(row[1:])
        return determinant(rows[1:])
    xs = range(len(crossings))
    coef = [Fraction(0)] * len(xs)
    for j in xs:                           # Lagrange interpolation
        basis, den = [Fraction(1)], Fraction(1)
        for k in xs:
            if k != j:
                basis = [Fraction(0)] + basis
                for i in range(len(basis) - 1):
                    basis[i] -= k * basis[i + 1]
                den *= j - k
        y = minor(Fraction(j))
        for i, b in enumerate(basis):
            coef[i] += y * b / den
    out = [int(c) for c in coef]
    while out and out[-1] == 0:
        out.pop()
    while out and out[0] == 0:
        out.pop(0)
    return [-c for c in out] if out and out[0] < 0 else out


def poly_text(p, quarters=True):
    """A polynomial in t as text: {exponent: coefficient}, the exponents in
    quarters (Jones) or whole (Alexander, given as a list from t^0)."""
    if not quarters:
        p = {4 * i: c for i, c in enumerate(p) if c}
    if not p:
        return "0"
    out = []
    for e, c in sorted(p.items()):
        q = Fraction(e, 4)
        x = "" if q == 0 else "t" if q == 1 else f"t^{q}" if q.denominator == 1 \
            else f"t^({q})"
        num = str(abs(c)) if abs(c) != 1 or not x else ""
        out.append(("- " if c < 0 else "+ ") + num + x)
    s = " ".join(out)
    return s[2:] if s.startswith("+ ") else "-" + s[2:]


def mirror_poly(p):
    return {-e: c for e, c in p.items()}


# The knots and links the closures give, each with the Jones polynomial of one
# hand (and for a link, one direction of its ropes). Names are the Rolfsen
# knot table's and, for links, Thistlethwaite's with Rolfsen's after.
# Checked offline against SnapPy 3.3.2 (identify() on each closure's
# complement, and the Jones polynomials of its table diagrams for the ones
# with no hyperbolic structure); not needed to run this script.
KNOWN = {
    "1": ("0_1", "unknot"),
    "t + t^3 - t^4": ("3_1", "trefoil (right-handed)"),
    "t^-2 - t^-1 + 1 - t + t^2": ("4_1", "figure-eight knot"),
    "t^2 + t^4 - t^5 + t^6 - t^7": ("5_1", "cinquefoil, the (2,5) torus knot"),
    "t - t^2 + 2t^3 - t^4 + t^5 - t^6": ("5_2", "three-twist knot"),
    "-t^-3 + 2t^-2 - 2t^-1 + 3 - 2t + 2t^2 - t^3": ("6_3", ""),
    "-t^-3 + t^-2 - t^-1 + 3 - t + t^2 - t^3": ("3_1#3_1*", "square knot"),
    "t^-4 - 4t^-3 + 6t^-2 - 7t^-1 + 9 - 7t + 6t^2 - 4t^3 + t^4":
        ("8_18", "the Carrick mat, a 3-lead 4-bight Turk's head"),
    "t^3 + t^5 - t^8": ("8_19", "the (3,4) torus knot"),
    "-t^-1 + 2 - t + 2t^2 - t^3 + t^4 - t^5": ("8_20", ""),
    "-t^(-1/2) - t^(1/2)": ("unlink", "two loops, not linked"),
    "-t^(1/2) - t^(5/2)": ("L2a1", "Hopf link"),
    "-t^(3/2) - t^(7/2) + t^(9/2) - t^(11/2)": ("L4a1", "Solomon link, the (2,4) torus link"),
    "-t^(-3/2) + t^(-1/2) - 2t^(1/2) + t^(3/2) - 2t^(5/2) + t^(7/2)":
        ("L5a1", "Whitehead link"),
    "-t^(-3/2) + 2t^(-1/2) - 2t^(1/2) + 2t^(3/2) - 3t^(5/2) + t^(7/2) - t^(9/2)":
        ("L6a1", "Rolfsen 6^2_3"),
    "-t^(3/2) + t^(5/2) - 2t^(7/2) + 2t^(9/2) - 2t^(11/2) + t^(13/2) - t^(15/2)":
        ("L6a2", "Rolfsen 6^2_2"),
    "-t^(5/2) - t^(9/2) + t^(11/2) - t^(13/2) + t^(15/2) - t^(17/2)":
        ("L6a3", "the (2,6) torus link"),
    "-t^(-3/2) + 2t^(-1/2) - 3t^(1/2) + 3t^(3/2) - 4t^(5/2) + 2t^(7/2) - 2t^(9/2) + t^(11/2)":
        ("L7a5", "Rolfsen 7^2_2"),
    "-t^(-1/2) + t^(1/2) - 2t^(3/2) + 2t^(5/2) - 3t^(7/2) + 2t^(9/2) - 2t^(11/2) + t^(13/2)":
        ("L7a6", "Rolfsen 7^2_1"),
    "-t^(-9/2) + 3t^(-7/2) - 4t^(-5/2) + 5t^(-3/2) - 6t^(-1/2) + 4t^(1/2) - 4t^(3/2) "
    "+ 2t^(5/2) - t^(7/2)": ("L8a8", "Rolfsen 8^2_7"),
}


def identify(n, closure):
    """(table name, common name, mirror): which knot or link the closure is.
    A knot's mirror image is marked *; a link is named whatever its hand and
    the directions of its ropes."""
    v = jones(n, closure)
    tries = [(v, False), (mirror_poly(v), True)]
    if closure == "own":                   # turn the 2nd rope round
        r = {e - 12 * linking(n): c for e, c in v.items()}
        tries += [(r, False), (mirror_poly(r), True)]
    for p, m in tries:
        hit = KNOWN.get(poly_text(p))
        if hit:
            name, common = hit
            if closure == "across" and m and poly_text(v) != poly_text(mirror_poly(v)):
                name += "*"
                common = common.replace("right-handed", "left-handed")
            return name, common
    raise ValueError(f"drawing {n}, {closure}: Jones polynomial {poly_text(v)} not in KNOWN")


def twist(f, g, s):
    """The bracket after one half twist of a pair of ends (s = +1 or -1)."""
    if s > 0:
        return padd(pmul({-3: -1}, f), pmul({-1: 1}, g)), pmul({1: 1}, g)
    return padd(pmul({3: -1}, f), pmul({1: 1}, g)), pmul({-1: 1}, g)


def canonical(f, g):
    """The bracket up to a factor of -A^3 (which a kink in a rope gives)."""
    low = min(list(f) + list(g))
    u = {-3 * (low // 3): 1}
    f, g = pmul(f, u), pmul(g, u)
    if (f or g)[min(f or g)] < 0:
        f, g = pmul(f, {0: -1}), pmul(g, {0: -1})
    return tuple(sorted(f.items())), tuple(sorted(g.items()))


TWISTS = 16


def orbit(n):
    out = set()
    for s in (1, -1):
        f, g = bracket(n)
        for _ in range(TWISTS + 1):
            out.add(canonical(f, g))
            f, g = twist(f, g, s)
    return out


def groups():
    """Drawings whose brackets agree once the ends are allowed to twist."""
    parent = list(range(256))

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    first = {}
    for n in range(256):
        for key in orbit(n):
            if key in first:
                parent[find(n)] = find(first[key])
            else:
                first[key] = n
    members = defaultdict(list)
    for n in range(256):
        members[find(n)].append(n)
    ordered = sorted(members.values(), key=min)
    return {n: gi + 1 for gi, ns in enumerate(ordered) for n in ns}, ordered


def index_names():
    names = {}
    for line in (HERE / "original/index.txt").read_text().splitlines():
        n, text = line.split(" ", 1)
        names[int(n)] = re.sub(r"\[[^]]*\]\s*", "", text).strip()
    return names


def drawing_names():
    names = {}
    for line in (HERE / "original/drawings.txt").read_text().splitlines():
        m = re.match(r'  (\d+)\s+(?:boxed in green, )?"([^"]+)"', line)
        if m:
            names[int(m[1])] = m[2]
    return names


def kind(name):
    """A name from the index with spelling and wording evened out."""
    s = name.lower().replace("carrack", "carrick").replace(" knot)", ")")
    return s.replace("(unknown type)", "(unknown)")


# What The Ashley Book of Knots (1944) calls the knotted groups. On the
# IGKT forum, Eric (NautiKnots) tied all 512 bends of the Carrick diagram,
# these 256 crossings with each rope's standing end at either end, and named
# each from Ashley ("Bends Based on the Carrick Bend Diagram", FORUM below).
# Moving a standing end changes which end is pulled, not the drawing, so one
# drawing carries a name for each lead. Eric's crossings A-H are this key's
# 6, 1, 5, 8, 7, 4, 3, 2, Eric's white rope the 1st and grey the 2nd: the
# figures of #1207, #1439 and #1445, read crossing by crossing, are
# drawings 195/199/227/231, 138/117 and 178/77. The other figures are gone
# from the forum, so the remaining groups are matched by elimination: Eric
# finds three Single Carrick Bends and two Whatnots, ties the Whatnot 8 ways
# and the Thief Knot 12, and those counts fit only as below. Ashley numbers
# also checked against Wikipedia.
FORUM = "https://discourse.igkt.net/t/bends-based-on-the-carrick-bend-diagram/6260"
BOOK = [
    # drawings naming the groups, Ashley's name, other names, how matched
    ((24,), "Reef Knot, #1402",
     "Thief Knot, #1207, with the standing ends on opposite sides (Eric)",
     "Eric's #1207 figure is drawings 195, 199, 227 and 231, all in this group"),
    ((26, 29), "Sheet Bend, #1431",
     "Left-Hand Sheet Bend, #1432, with the bight's lead reversed (Ashley's name; "
     "Eric notes it is the same knot, not the other hand); with the other lead "
     "reversed, the Eskimo Sheet Bend (Eric's name) or Lapp Bend (knotsaver)",
     "the index"),
    ((117, 138), "Carrick Bend, #1439",
     "with a lead reversed, #1428, the Double Coin Knot or Pretzel Knot, #2283 (Eric)",
     "Eric's #1439 figures: Ashley's own, the left-handed one, is 138; 117 is its "
     "mirror image"),
    ((77,), "Single Carrick Bend, #1445", "",
     "Eric's #1445 figures: Ashley's own is 178; 77 is its mirror image"),
    ((74, 118), "Single Carrick Bend, #1443 or #1444", "",
     "by elimination; which of the two needs Ashley's figures"),
    ((106, 114), "Single Carrick Bend, #1443 or #1444", "",
     "by elimination; which of the two needs Ashley's figures"),
    ((73, 109), "Whatnot, #1406 or #1407",
     "Granny Knot, #1405, with the standing ends on the same side (Eric)",
     "by elimination, with Eric's 8 Whatnot ties; the index calls 109 a single "
     "carrick bend"),
    ((101, 154), "Whatnot, #1406 or #1407",
     "Granny Knot, #1405, with the standing ends on the same side (Eric)",
     "by elimination, with Eric's 8 Whatnot ties"),
]


# Two names in the index clash with the drawings' mirror images and with
# Ashley. original/index.txt keeps them as written; these are the readings
# used beside them.
CORRECTED = {
    109: ("whatnot",
          "the mirror image of 73, which the index calls a whatnot, and a mirror "
          "image keeps its name; Ashley's Whatnot (Eric's counts), not a Single "
          "Carrick Bend"),
    118: ("single carrick bend (unknown)",
          "the mirror image of 74, a single carrick bend (unknown type); Ashley's "
          "Single Carrick Bend, while the Carrick Bend itself is only 117 and 138"),
}


# Ashley numbers for every knotted drawing, one for each lead: the standing
# ends on the same side, and on opposite sides (diagonal). Eric's figures show
# Ashley's #1207, #1439 and #1445 with the standing ends on opposite sides;
# the Reef Knot and Granny Knot have them on the same side, the Thief Knot
# and Whatnot opposite (Eric; Ashley on the Whatnot: "the ends are
# diagonally opposite"). Suffixes are Eric's: m the mirror image of Ashley's
# figure, r the lead reversed. Where the hand of Ashley's figure is not known
# no m is given; where the number is not known both are given.
LEADS = [
    # drawings naming the groups, same side, opposite
    ((24,), "1402", "1207"),
    ((26, 29), "1431 or 1432", "1431 or 1432"),
    ((138,), "1428m", "1439"),
    ((117,), "1428", "1439m"),
    ((178, 150), "1445r", "1445"),
    ((77, 105), "1445rm", "1445m"),
    ((74, 118, 106, 114), "1443r or 1444r", "1443 or 1444"),
    ((73, 109, 101, 154), "1405", "1406 or 1407"),
]


def abok(n, group_of):
    """(same side, opposite) Ashley numbers for drawing n, or None if it is
    not a knot. A drawing listed by number takes its own entry before its
    group's."""
    for ns, same, opposite in LEADS:
        if n in ns:
            return same, opposite
    for ns, same, opposite in LEADS:
        if group_of[n] in {group_of[m] for m in ns} and not {138, 117, 178, 77} & set(ns):
            return same, opposite
    return None


def corrected(names):
    return {n: CORRECTED[n][0] if n in CORRECTED else name for n, name in names.items()}


def book_names(group_of):
    """Each knotted group's entry in BOOK."""
    out = {}
    for ns, ashley, other, how in BOOK:
        for n in ns:
            out[group_of[n]] = (ashley, other, how)
    return out


def analyse():
    group_of, members = groups()
    mirror = {g: group_of[255 - ns[0]] for g, ns in enumerate(members, 1)}
    names, drawn = index_names(), drawing_names()
    return group_of, members, mirror, names, drawn


def knots_txt(group_of, mirror, names, drawn):
    lines = ["Every drawing. Crossing k is circled when bit k-1 of the number is 1.",
             "Over and under are read along each rope from its start, the first",
             "pass going over unless circled. lk = linking number of the two ropes",
             "closed on themselves. Group = knot, ends allowed to twist (groups.txt).",
             "Own, across = the link and the knot the drawing closes to (closures.txt).",
             "ABOK = Ashley's number with the standing ends on the same side / on",
             "opposite sides, for the 50 drawings that make a knot (BOOK, LEADS in",
             "knot_crossings.py; m = mirror image of Ashley's figure, r = lead reversed).",
             "",
             f"{'n':>3}  {'circled':<15}  {'1st rope':<8}  {'2nd rope':<8}  {'lk':>2}  "
             f"{'group':>5}  {'own':<6}  {'across':<8}  {'ABOK':<31}  name on the page",
             ""]
    for n in range(256):
        circled = ",".join(str(k) for k in CROSSINGS if n >> (k - 1) & 1) or "-"
        w1, w2 = words(n)
        name = names.get(n) or (f'"{drawn[n]}" (on the drawing)' if n in drawn else "")
        own, across = (identify(n, c)[0] for c in CLOSURES)
        a = abok(n, group_of)
        a = f"{a[0]} / {a[1]}" if a else "-"
        lines.append(f"{n:>3}  {circled:<15}  {w1:<8}  {w2:<8}  {linking(n):>2}  "
                     f"{group_of[n]:>5}  {own:<6}  {across:<8}  {a:<31}  {name}".rstrip())
    return "\n".join(lines) + "\n"


def closure_classes(closure):
    """The knots or links one closure gives, in order of crossings, each with
    its drawings and the distinct Alexander and Jones polynomials found."""
    found = defaultdict(list)
    for n in range(256):
        found[identify(n, closure)].append(n)
    order = [name for name, _ in KNOWN.values()]
    out = []
    for (name, common), ns in found.items():
        base = name if name in order else name[:-1]
        out.append({
            "name": name, "common": common, "drawings": ns,
            "alexander": sorted({tuple(alexander(n, closure)) for n in ns}),
            "jones": sorted({poly_text(jones(n, closure)) for n in ns}, key=len),
            "det": abs(sum(c * (-1) ** i for i, c in enumerate(alexander(ns[0], closure)))),
            "key": (order.index(base), name != base),
        })
    return sorted(out, key=lambda c: c["key"])


CLOSURE_TEXT = {
    "own": "each rope's end joined back to its own start: two loops, a link",
    "across": "each rope's end joined on to the other rope's start: one loop, a knot",
}


def closures_txt(names, group_of):
    lines = ["Every drawing closed up, its four ends joined in the two ways that add",
             "no crossing:", ""]
    for c in CLOSURES:
        lines.append(f"  {c:<7} {CLOSURE_TEXT[c]}")
    lines += ["",
              "Each closure is named by its Jones polynomial, which differs between",
              "every knot and link here; the names were also checked with SnapPy.",
              "* marks a knot's mirror image (the hand whose Jones polynomial is not",
              "the one in knot_crossings.py). A link is named whatever its hand and",
              "the directions of its ropes, so it can show more than one Jones",
              "polynomial and, as the directions change it, Alexander polynomial.",
              "det = |Alexander(-1)| = |Jones(-1)|.", ""]
    for c in CLOSURES:
        classes = closure_classes(c)
        trivial = len(classes[0]["drawings"])
        lines.append(f"{c.upper()}: {CLOSURE_TEXT[c]}. "
                     + (f"{trivial} unlinked, {256 - trivial} linked."
                        if c == "own" else f"{trivial} unknots, {256 - trivial} knots."))
        lines.append("")
        for k in classes:
            head = f"  {k['name']}" + (f", {k['common']}" if k["common"] else "")
            lines.append(f"{head}: {len(k['drawings'])} drawing"
                         f"{'s' if len(k['drawings']) > 1 else ''}, det {k['det']}")
            for a in k["alexander"]:
                lines.append(f"    Alexander  {poly_text(list(a), quarters=False)}")
            for j in k["jones"]:
                lines.append(f"    Jones      {j}")
            ns = k["drawings"]
            for i in range(0, len(ns), 16):
                lines.append("    " + " ".join(f"{n:>3}" for n in ns[i:i + 16]))
            lines.append("")
    lines += ["The drawings named in the index, closed, and what The Ashley Book of",
              "Knots calls them, as matched by Eric (NautiKnots) on the IGKT forum",
              "(knot_crossings.py, BOOK, says how):", "",
              f"  {'n':>3}  {'own':<6}  {'across':<8}  name in the index"]
    for n in sorted(names):
        own, across = (identify(n, c)[0] for c in CLOSURES)
        lines.append(f"  {n:>3}  {own:<6}  {across:<8}  {names[n]}"
                     + (f"  -> {CORRECTED[n][0]}" if n in CORRECTED else ""))
        lines.append(f"  {'':>3}  {'':<6}  {'':<8}    Ashley: "
                     f"{book_names(group_of)[group_of[n]][0]}")
    return "\n".join(lines) + "\n"


def group_names(ns, names, drawn):
    out = [f"{names[n]} ({n})" for n in ns if n in names]
    out += [f'"{drawn[n]}" ({n}, drawing)' for n in ns if n in drawn and n not in names]
    return out


def groups_txt(members, mirror, names, drawn):
    lines = ["Each group holds the drawings whose Kauffman brackets agree once the",
             "ends of a rope may be twisted about each other. Different brackets",
             "prove different knots; the same bracket does not prove the same knot.",
             "Mirror = the group of 255 - n, every crossing turned over.", ""]
    for g, ns in enumerate(members, 1):
        m = mirror[g]
        lks = sorted({abs(linking(n)) for n in ns})
        lines.append(f"Group {g}: {len(ns)} drawing{'s' if len(ns) > 1 else ''}, mirror "
                     f"{'itself' if m == g else f'group {m}'}, |lk| "
                     f"{', '.join(map(str, lks))}"
                     + (", alternating" if any(alternating(n) for n in ns) else ""))
        for name in group_names(ns, names, drawn):
            lines.append(f"  named {name}")
        for i in range(0, len(ns), 16):
            lines.append("  " + " ".join(f"{n:>3}" for n in ns[i:i + 16]))
        lines.append("")
    return "\n".join(lines)


def checks_txt(group_of, members, mirror, names):
    last = max(names)
    by_kind = defaultdict(list)
    for n, name in names.items():
        by_kind[kind(name)].append(n)
    lines = [f"The index names {len(names)} drawings, from {min(names)} to {last}.", "",
             "Each name, and the groups its drawings fall in:", ""]
    for k, ns in sorted(by_kind.items(), key=lambda t: min(t[1])):
        gs = sorted({group_of[n] for n in ns})
        if len(gs) == 1:
            verdict = "one group"
        elif len(gs) == 2 and mirror[gs[0]] == gs[1]:
            verdict = "a group and its mirror"
        else:
            verdict = f"{len(gs)} groups"
        lines.append(f"  {k}: {', '.join(map(str, sorted(ns)))} -> group "
                     f"{', '.join(map(str, gs))} ({verdict})")
    lines += ["", f"Drawings up to {last} in a named group but not in the index:", ""]
    named_groups = {group_of[n] for n in names}
    missing = [n for n in range(last + 1) if group_of[n] in named_groups and n not in names]
    lines.append("  " + (", ".join(map(str, missing)) if missing else "none"))
    lines += ["", "Names given to drawings that are mirror images of each other:", ""]
    for a in sorted(names):
        for b in sorted(names):
            if a < b and kind(names[a]) != kind(names[b]) and \
                    mirror[group_of[a]] == group_of[b] and group_of[a] != group_of[b]:
                lines.append(f"  {a} {names[a]}  <->  {b} {names[b]}")
    lines += ["", "Clashes resolved (original/index.txt is left as written):", ""]
    for n, (name, why) in CORRECTED.items():
        lines.append(f"  {n} {names[n]}  ->  {name}")
        lines.append(f"      {why}")
    fixed = corrected(names)
    by_fixed = defaultdict(list)
    for n, name in fixed.items():
        by_fixed[kind(name)].append(n)
    lines += ["", "Each name once they are resolved:", ""]
    for k, ns in sorted(by_fixed.items(), key=lambda t: min(t[1])):
        gs = sorted({group_of[n] for n in ns})
        mirrored = all(mirror[g] in gs for g in gs)
        lines.append(f"  {k}: {', '.join(map(str, sorted(ns)))} -> group "
                     f"{', '.join(map(str, gs))}"
                     + (" (closed under mirror images)" if mirrored else ""))
    alt = [n for n in range(256) if alternating(n)]
    lines += ["", f"Alternating drawings (over, under, over ... along both ropes): "
              f"{', '.join(map(str, alt))}", ""]
    return "\n".join(lines)


# Drawing ------------------------------------------------------------------

def spline(path):
    """A smooth path through the points (Catmull-Rom as cubic Beziers)."""
    p = [point(w) for w in path]
    p = [p[0]] + p + [p[-1]]
    d = f"M{p[1][0]} {p[1][1]}"
    for i in range(1, len(p) - 2):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p[i - 1], p[i], p[i + 1], p[i + 2]
        d += (f" C{x1 + (x2 - x0) / 6:.0f} {y1 + (y2 - y0) / 6:.0f}"
              f" {x2 - (x3 - x1) / 6:.0f} {y2 - (y3 - y1) / 6:.0f} {x2} {y2}")
    return d


def overs(n, half=42):
    out = []
    for k in CROSSINGS:
        r, _, (dx, dy), (x, y) = PASSES[over(n, k)]
        s = half / math.hypot(dx, dy)
        seg = (f"M{x - dx * s:.0f} {y - dy * s:.0f}L{x + dx * s:.0f} {y + dy * s:.0f}")
        out.append(f'<path class="h" d="{seg}"/><path class="r{r + 1}" d="{seg}"/>')
        if n >> (k - 1) & 1:
            out.append(f'<circle class="c" cx="{x}" cy="{y}" r="44"/>')
    return "".join(out)


DEFS = (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
        f'<path id="rope1" class="r1" d="{spline(ROPES[0][1])}"/>'
        f'<path id="rope2" class="r2" d="{spline(ROPES[1][1])}"/>'
        f'</defs></svg>')
VIEW = "0 110 680 960"


def drawing(n):
    return (f'<svg viewBox="{VIEW}" role="img" aria-label="drawing {n}">'
            f'<use href="#rope1"/><use href="#rope2"/>{overs(n)}</svg>')


# Where the key writes each crossing's number.
LABELS = {1: (240, 285), 2: (560, 340), 3: (340, 430), 4: (60, 640),
          5: (500, 670), 6: (300, 740), 7: (90, 915), 8: (490, 870)}


def key_drawing():
    labels = "".join(f'<text x="{x}" y="{y}">{k}</text>' for k, (x, y) in LABELS.items())
    return (f'<svg class="key" viewBox="-40 60 760 1040" role="img" '
            f'aria-label="The key: two ropes and their 8 crossings">'
            f'<use href="#rope1"/><use href="#rope2"/>{overs(0)}'
            f'<circle class="r2 end" cx="75" cy="215" r="20"/>'
            f'<circle class="r1 end" cx="530" cy="990" r="20"/>'
            f'<path class="r2" d="M600 245 L640 265 L605 290"/>'
            f'<path class="r1" d="M38 985 L30 1030 L75 1030"/>'
            f'<text x="75" y="150">2nd</text><text x="600" y="1045">1st</text>'
            f'{labels}</svg>')


def rolfsen(text):
    """Rolfsen's link names, 6^2_3, as 6 with 2 above and 3 below."""
    return re.sub(r"(\d)\^(\d)_(\d+)", r"\1<sup>\2</sup><sub>\3</sub>", text)


def poly_html(text):
    """Exponents and subscripts raised and lowered, minus signs typeset."""
    text = re.sub(r"t\^\(?(-?[\d/]+)\)?", r"t<sup>\1</sup>", escape(text))
    text = re.sub(r"(\d)\^(\d)_(\d+)", r"\1<sup>\2</sup><sub>\3</sub>", text)
    text = re.sub(r"(\d)_(\d+)", r"\1<sub>\2</sub>", text)
    return text.replace("-", "&minus;").replace("#", " # ")


# The two ways of joining the ends, drawn outside the key.
CLOSE_PATHS = {
    "own": ["M75 215 C60 40 660 60 640 265", "M530 990 C600 1120 -20 1120 30 1030"],
    "across": ["M640 265 C760 300 700 1000 530 990", "M30 1030 C-60 1000 -40 230 75 215"],
}


def closure_drawing(n, closure):
    arcs = "".join(f'<path class="cl" d="{d}"/>' for d in CLOSE_PATHS[closure])
    return (f'<svg class="closure" viewBox="-80 30 820 1110" role="img" '
            f'aria-label="drawing {n} with its ends joined {closure}">'
            f'{arcs}<use href="#rope1"/><use href="#rope2"/>{overs(n)}</svg>')


def book_rows(group_of, members):
    rows = []
    for ns, ashley, other, how in BOOK:
        gs = sorted({group_of[n] for n in ns})
        draw = sorted(n for g in gs for n in members[g - 1])
        rows.append(
            f'<tr><td>{", ".join(f"<a href=#g{g}>{g}</a>" for g in gs)}</td>'
            f'<td><b>{escape(ashley)}</b></td><td>{escape(other) or "&mdash;"}</td>'
            f'<td>{escape(how)}</td>'
            f'<td class="members">{" ".join(f"<a href=#d{n}>{n}</a>" for n in draw)}</td></tr>')
    return "\n".join(rows)


def page(group_of, members, mirror, names, drawn, results):
    rows = []
    for g, ns in enumerate(members, 1):
        nm = group_names(ns, names, drawn)
        m = mirror[g]
        lks = ", ".join(str(v) for v in sorted({abs(linking(n)) for n in ns}))
        links = " ".join(f'<a href="#d{n}">{n}</a>' for n in ns)
        rows.append(
            f'<tr id="g{g}"><td class="num">{g}</td>'
            f'<td><div class="mini">{drawing(ns[0])}</div></td>'
            f'<td>{"<br>".join(escape(x) for x in nm) or "&mdash;"}</td>'
            f'<td class="num">{"itself" if m == g else f"<a href=#g{m}>{m}</a>"}</td>'
            f'<td class="num">{lks}</td>'
            f'<td class="members">{len(ns)}: {links}</td></tr>')
    closed = {}
    for c in CLOSURES:
        crows = []
        for k in closure_classes(c):
            ns = k["drawings"]
            links = " ".join(f'<a href="#d{n}">{n}</a>' for n in ns)
            crows.append(
                f'<tr id="{c}-{k["name"].replace("#", "-").replace("*", "m")}">'
                f'<td><b>{poly_html(k["name"])}</b></td>'
                f'<td>{rolfsen(escape(k["common"])) or "&mdash;"}</td>'
                f'<td class="num">{k["det"]}</td>'
                f'<td class="poly">{"<br>".join(poly_html(poly_text(list(a), False)) for a in k["alexander"])}</td>'
                f'<td class="poly">{"<br>".join(poly_html(j) for j in k["jones"])}</td>'
                f'<td class="members">{len(ns)}: {links}</td></tr>')
        closed[c] = "\n".join(crows)
    named_rows = "\n".join(
        f'<tr><td class="num"><a href="#d{n}">{n}</a></td><td>{escape(names[n])}'
        + (f'<br><b>&rarr; {escape(CORRECTED[n][0])}</b>' if n in CORRECTED else '')
        + '</td>'
        f'<td>{escape(book_names(group_of)[group_of[n]][0])}</td>'
        + "".join(f'<td>{poly_html(identify(n, c)[0])}</td>' for c in CLOSURES) + "</tr>"
        for n in sorted(names))
    cards = []
    for n in range(256):
        label = names.get(n) or (f"&ldquo;{escape(drawn[n])}&rdquo;" if n in drawn else "")
        own, across = (poly_html(identify(n, c)[0]) for c in CLOSURES)
        a = abok(n, group_of)
        a = (f'<i class="abok">ABOK {escape(a[0])} &middot; {escape(a[1])}</i>'
             if a else "")
        cards.append(f'<figure id="d{n}"{" class=named" if n in names else ""}>'
                     f'{drawing(n)}<figcaption><b>{n}</b> '
                     f'<a href="#g{group_of[n]}">g{group_of[n]}</a>'
                     f'<a href="turn.html#{n}">3D</a>'
                     f'<i>{own} &middot; {across}</i>{a}'
                     f'<span>{escape(label) if n in names else label}</span>'
                     f'</figcaption></figure>')
    return (PAGE.replace("{defs}", DEFS).replace("{key}", key_drawing())
            .replace("{checks}", f"<pre>{escape(results['checks.txt'].decode())}</pre>")
            .replace("{groups}", "\n".join(rows))
            .replace("{close_own}", closure_drawing(117, "own"))
            .replace("{close_across}", closure_drawing(117, "across"))
            .replace("{own}", closed["own"]).replace("{across}", closed["across"])
            .replace("{named}", named_rows)
            .replace("{book}", book_rows(group_of, members)).replace("{forum}", FORUM)
            .replace("{cards}", "\n".join(cards))).encode()


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Knot Crossings</title>
<style>
:root { --bg: #fbfaf7; --fg: #1d1d1b; --muted: #5d5b55; --rule: #dedbd3;
        --link: #2a5d9f; --code: #f1efe9; --r1: #b4462b; --r2: #2a5d9f;
        --mark: #c9a227; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #161615; --fg: #e8e6e1; --muted: #a29f97; --rule: #34332f;
          --link: #8ab4f0; --code: #20201e; --r1: #e8866b; --r2: #8ab4f0;
          --mark: #d9b84a; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
       font: 17px/1.55 Georgia, "Times New Roman", serif; }
main { max-width: 60rem; margin: 0 auto; padding: 2rem 16px 4rem; }
h1 { font-size: 2.2rem; margin: 0 0 .3rem; }
h2 { font-size: 1.4rem; margin: 2.6rem 0 .4rem; padding-top: 1rem;
     border-top: 1px solid var(--rule); }
a { color: var(--link); }
.back { margin: 0 0 1.5rem; font-family: system-ui, sans-serif; font-size: .95rem; }
pre { background: var(--code); padding: .9rem 1rem; overflow-x: auto;
      font: 13px/1.4 ui-monospace, Menlo, Consolas, monospace; border-radius: 4px; }
svg path, svg use { fill: none; stroke-width: 18; stroke-linecap: round;
                    stroke-linejoin: round; }
.r1 { stroke: var(--r1); } .r2 { stroke: var(--r2); }
.h { stroke: var(--bg); stroke-width: 48; stroke-linecap: butt; }
.c { fill: none; stroke: var(--mark); stroke-width: 7; }
.end { fill: none; stroke-width: 10; }
.key { display: block; width: 100%; max-width: 300px; margin: 1rem auto; }
.key text { fill: var(--fg); font: 54px Georgia, serif; text-anchor: middle;
             dominant-baseline: central; }
.lay { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 1.5rem;
       align-items: start; }
@media (max-width: 720px) { .lay { grid-template-columns: 1fr; } }
.wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .9rem;
        font-family: system-ui, sans-serif; }
th, td { border-bottom: 1px solid var(--rule); padding: .35rem .4rem;
         text-align: left; vertical-align: middle; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td.members { font-size: .8rem; line-height: 1.6; }
.mini svg { width: 46px; display: block; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr));
        gap: .5rem; font-family: system-ui, sans-serif; }
figure { margin: 0; padding: .3rem; border: 1px solid var(--rule); border-radius: 4px; }
figure.named { border-color: var(--mark); }
figure:target { outline: 2px solid var(--link); }
figure svg { display: block; width: 100%; }
figcaption { font-size: .75rem; line-height: 1.3; }
figcaption a { margin-left: .3rem; color: var(--muted); }
figcaption span { display: block; color: var(--muted); }
figcaption i { display: block; font-style: normal; }
figcaption i.abok { color: var(--link); }
h3 { font-size: 1.1rem; margin: 1.8rem 0 .4rem; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 34rem;
        margin: 1rem auto; }
.pair figure { border: 0; }
.pair figcaption { font-size: .85rem; text-align: center; }
.closure { display: block; width: 100%; }
svg path.cl { stroke: var(--muted); stroke-width: 10; stroke-dasharray: 26 18; }
td.poly { font-size: .8rem; min-width: 14rem; }
</style>
</head>
<body>
{defs}
<main>
<h1>Knot Crossings</h1>
<p class="back"><a href="https://gernreich.github.io/">&larr; All projects</a>
&middot; <a href="turn.html">Turn the ropes in 3D &rarr;</a></p>

<div class="lay">
<div>
<p>Two ropes, drawn once and crossing each other 8 times. Every crossing can go
either way, over or under, so the one drawing holds 2<sup>8</sup> = 256 knots.
The author drew all 256 by hand on yellow legal paper, numbered 0 to 255, and
marked each crossing that goes the other way with a small circle. The circles
are the number written in binary, crossing 1 for 1, crossing 2 for 2,
crossing 3 for 4, and so on up to crossing 8 for 128. The knots the author
recognised are listed in an index: the square knot, the sheet bend, the
Carrick bend and its relatives.</p>
<p>Here <a href="knot_crossings.py">knot_crossings.py</a> works the 256 out
again from the key, and sorts them into knots with the Kauffman bracket, a
number-like invariant that stays the same however a knot is redrawn. Without a circle, a crossing goes over for
the rope that reaches it first, following the 1st rope and then the 2nd; that
is the only reading under which the Carrick bend, number 117, comes out over,
under, over, under all the way along both ropes. Reading every crossing the
other way gives the mirror image of every drawing, and changes no name.</p>
</div>
{key}
</div>

<h2>The index, checked</h2>
<p>The square knot, which is its own mirror image, lands in a group that is
its own mirror, and the sheet bend in a group and its mirror image. No drawing
up to 122, the last one indexed, is in a named group without being named.
Three pairs of names turn out to be mirror images of one another, and two of
those pairs clash: 109, a single carrick bend (reformed constrictor) in the
index, is the mirror image of 73, a whatnot; and 118, a Carrick bend, is the
mirror image of 74, a single carrick bend. A mirror image keeps its name, and
the names in <i>The Ashley Book of Knots</i> (below) settle both: 109 is a
whatnot and 118 a single carrick bend. Read that way, the reformed
constrictor is one knot, 77 and 105, and no two mirror images carry the
names of different knots (106 and 114 differ only by &ldquo;unknown&rdquo;). The index itself is kept as written.</p>
{checks}

<h2>The groups</h2>
<p>Each group holds the drawings with the same Kauffman bracket, counting two
drawings as one knot when they differ only by the ends of a rope being turned
about each other, as a rope&rsquo;s two ends can be in the hand. Different
brackets prove different knots; the same bracket strongly suggests, but does not
prove, the same knot. |lk| is how many times the ropes wind round each other
when each is closed on itself. The drawing shown is the group&rsquo;s first.
Names in quotes are written beside the drawings rather than in the index.</p>
<div class="wrap"><table>
<tr><th>Group</th><th></th><th>Named</th><th>Mirror</th><th>|lk|</th><th>Drawings</th></tr>
{groups}
</table></div>

<h2>Closing the ends</h2>
<p>A rope with two loose ends can always be untied, so to ask whether a
drawing is really knotted its ends have to be joined. The four ends lie round
the outside of the drawing, and there are two ways to join them without making
a new crossing: each rope&rsquo;s end back to its own start, which gives two
closed loops, a <em>link</em>; or each rope&rsquo;s end on to the other
rope&rsquo;s start, which gives one closed loop, a <em>knot</em>. Every drawing
is closed both ways. Shown here with the Carrick bend, 117.</p>
<div class="pair">
<figure>{close_own}<figcaption>Own: two loops. The Carrick bend closes to the link L8a8.</figcaption></figure>
<figure>{close_across}<figcaption>Across: one loop. The Carrick bend closes to 8<sub>18</sub>, the Carrick mat.</figcaption></figure>
</div>
<p>Each closure is named by its Jones polynomial, which here differs between
every knot and link that turns up, and checked with its Alexander polynomial
and determinant, which must agree with it. The names were also checked against
SnapPy, which also untangles every unlinked pair to no crossings at all.
Knot names are from the Rolfsen table, with * marking the mirror image of the
knot without it; link names are Thistlethwaite&rsquo;s. The square knot and
8<sub>20</sub> share their Alexander polynomial and determinant; only the
Jones polynomial tells them apart. A link is the same link whichever way its ropes run,
but its polynomials are not, so a link can show more than one. Mirror-image
drawings, <i>n</i> and 255&nbsp;&minus;&nbsp;<i>n</i>, always close to mirror
images.</p>

<h3>Own ends joined: links</h3>
<div class="wrap"><table>
<tr><th>Link</th><th>Known as</th><th>det</th><th>Alexander</th><th>Jones</th><th>Drawings</th></tr>
{own}
</table></div>

<h3>Ends joined across: knots</h3>
<div class="wrap"><table>
<tr><th>Knot</th><th>Known as</th><th>det</th><th>Alexander</th><th>Jones</th><th>Drawings</th></tr>
{across}
</table></div>

<h3>The index, closed</h3>
<p>A name in the index belongs to the knot in the hand, with its ends free to
turn; the closures depend on how the ends lie in the drawing, so drawings with
one name can close differently.</p>
<p>The <q>In Ashley</q> column is explained in the next section.</p>
<div class="wrap"><table>
<tr><th>Drawing</th><th>Name in the index</th><th>In Ashley</th><th>Own</th><th>Across</th></tr>
{named}
</table></div>

<h2>Names in the book</h2>
<p><i>The Ashley Book of Knots</i> (1944) works from the same diagram. Ashley
draws the reef knot, sheet bend, Carrick bend and granny knot on it
(#1549&ndash;1552) and notes that an eight-crossing knot allows 256
over-and-under arrangements. In 2025, Eric (NautiKnots on the forum of the
International Guild of Knot Tyers) tied all of them, each with the standing
ends on the same side and on opposite sides, and named every bend that held
from Ashley: <a href="{forum}">Bends Based on the Carrick Bend Diagram</a>.
Which end is standing changes how the knot is pulled, not the drawing, so one
drawing can carry two names, one for each lead. The names below are
Eric&rsquo;s, with one more from knotsaver in the same thread.</p>
<p>Eric&rsquo;s crossings A to H are crossings 6, 1, 5, 8, 7, 4, 3 and 2 of
the key. Eric&rsquo;s figures of the Thief Knot, the Carrick Bend and the third Single
Carrick Bend, read crossing by crossing, come out as drawings here, each in
the group this page had already put it in. The other figures no longer load
on the forum, so the rest are matched by elimination: Eric finds three Single
Carrick Bends and two Whatnots, and ties the Whatnot 8 ways and the Thief
Knot 12, which fits only one way. The count agrees with this page:
of the 512 bends, 100 held and the rest fell apart, and groups 1 to 6 here
hold 206 drawings, which leaves 50 knotted drawings, 100 with both leads. The Ashley numbers are Eric&rsquo;s, and
Wikipedia&rsquo;s where it gives them, not checked against the book.</p>
<div class="wrap"><table>
<tr><th>Groups</th><th>Ashley</th><th>Other names</th><th>Matched by</th><th>Drawings</th></tr>
{book}
</table></div>

<h2>All 256</h2>
<p>Under each drawing: the link and the knot it closes to (own &middot;
across), and, for the 50 drawings that make a knot, Ashley&rsquo;s number
with the standing ends on the same side &middot; on opposite sides. In those,
m marks the mirror image of Ashley&rsquo;s figure and r the lead reversed
(Eric&rsquo;s notation); <q>1443 or 1444</q> and <q>1406 or 1407</q> wait on
Ashley&rsquo;s figures. The other 206 drawings, by Eric&rsquo;s count, fall
apart when pulled.</p>
<p>Drawn from the key, with the crossings the author circled ringed in yellow
and the drawings named in the index outlined. The two ropes keep their colours: the 1st in
red, the 2nd in blue. The originals are in <a href="scans/knot-crossings.pdf">the
scan</a>; the index and the notes beside the drawings are transcribed in
<a href="original/index.txt">original/index.txt</a> and
<a href="original/drawings.txt">original/drawings.txt</a>.</p>
<div class="grid">
{cards}
</div>
<p class="credit" style="margin-top:2em;font-size:0.85em;opacity:0.75">The drawings are Michael Gernreich's; <a href="https://www.anthropic.com/claude">Claude</a> (Anthropic), working in Claude Code, co-wrote the transcriptions, the code and the documentation that present them. Commits Claude made carry a <code>Co-Authored-By: Claude</code> line.</p>
</main>
</body>
</html>
"""


# The 3D view ----------------------------------------------------------------

def turn_info(n, group_of, names, drawn):
    """What the 3D view says about drawing n, as HTML."""
    g = group_of[n]
    book = book_names(group_of).get(g)
    a = abok(n, group_of)
    lines = [f'<b>{n}</b> &middot; <a href="index.html#g{g}">group {g}</a> &middot; '
             f'<a href="index.html#d{n}">card</a>']
    if book:
        lines.append(f'<b>{escape(book[0])}</b>'
                     + (f' &middot; {escape(book[1])}' if book[1] else ''))
        lines.append(f'ABOK {escape(a[0])} with the standing ends on the same side, '
                     f'{escape(a[1])} on opposite sides')
    else:
        lines.append("Not in Ashley: by Eric&rsquo;s count it falls apart when pulled")
    if n in names:
        lines.append(f'Index: {escape(names[n])}'
                     + (f' &rarr; {escape(CORRECTED[n][0])}' if n in CORRECTED else ''))
    if n in drawn:
        lines.append(f'Written on the drawing: &ldquo;{escape(drawn[n])}&rdquo;')
    for c in CLOSURES:
        name, common = identify(n, c)
        lines.append(f'Ends joined {c}: {poly_html(name)}'
                     + (f' ({rolfsen(escape(common))})' if common else ''))
    return "<br>".join(lines)


def turn_page(group_of, names, drawn):
    import json
    ropes = []
    i = 0
    for _, path in ROPES:
        pts = []
        for w in path:
            x, y = point(w)
            if isinstance(w, int):
                pts.append([x, y, i])
                i += 1
            else:
                pts.append([x, y, -1])
        ropes.append(pts)
    data = {
        "ropes": ropes,
        "passes": [[r, k, list(d), list(p)] for r, k, d, p in PASSES],
        "at": {k: AT[k] for k in CROSSINGS},
        "close": {c: [[float(v) for v in re.findall(r"-?\d+", d)] for d in ds]
                  for c, ds in CLOSE_PATHS.items()},
        "closePaths": CLOSE_PATHS,
        "info": [turn_info(n, group_of, names, drawn) for n in range(256)],
    }
    return (TURN.replace("{defs}", DEFS)
            .replace("{data}", json.dumps(data, separators=(",", ":")))).encode()


TURN = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Knot Crossings 3D</title>
<style>
:root { --bg: #fbfaf7; --fg: #1d1d1b; --muted: #5d5b55; --rule: #dedbd3;
        --link: #2a5d9f; --panel: #f1efe9; --r1: #b4462b; --r2: #2a5d9f;
        --join: #8f8c84; --mark: #c9a227; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #161615; --fg: #e8e6e1; --muted: #a29f97; --rule: #34332f;
          --link: #8ab4f0; --panel: #20201e; --r1: #e8866b; --r2: #8ab4f0;
          --join: #8f8c84; --mark: #d9b84a; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
       font: 16px/1.5 Georgia, "Times New Roman", serif; }
main { max-width: 76rem; margin: 0 auto; padding: 1.5rem 16px 3rem; }
h1 { font-size: 1.9rem; margin: 0 0 .2rem; }
a { color: var(--link); }
.back { margin: 0 0 1rem; font-family: system-ui, sans-serif; font-size: .95rem; }
.lay { display: grid; grid-template-columns: minmax(0, 1fr) 19rem; gap: 1.2rem;
       align-items: start; }
@media (max-width: 760px) { .lay { grid-template-columns: 1fr; } }
.stage { position: relative; background: var(--panel); border: 1px solid var(--rule);
         border-radius: 6px; overflow: hidden; }
#view { display: block; width: 100%; height: min(78vh, 820px); touch-action: none;
        cursor: grab; }
.hint { position: absolute; left: 10px; bottom: 8px; margin: 0; color: var(--muted);
        font: .78rem system-ui, sans-serif; pointer-events: none; }
.panel { font-family: system-ui, sans-serif; font-size: .9rem; }
.pick { display: flex; gap: .4rem; align-items: center; margin-bottom: .8rem; }
.pick input { width: 5rem; font: inherit; font-size: 1.2rem; padding: .2rem .4rem;
              background: var(--bg); color: var(--fg); border: 1px solid var(--rule);
              border-radius: 4px; }
button { font: inherit; padding: .3rem .7rem; background: var(--bg); color: var(--fg);
         border: 1px solid var(--rule); border-radius: 4px; cursor: pointer; }
fieldset { border: 1px solid var(--rule); border-radius: 4px; margin: 0 0 .7rem;
           padding: .3rem .6rem .5rem; }
legend { color: var(--muted); padding: 0 .3rem; }
label { display: inline-block; margin: .15rem .9rem .15rem 0; cursor: pointer; }
#info { font-family: Georgia, serif; font-size: .92rem; line-height: 1.45;
        margin: .8rem 0; }
#flat { display: block; width: 100%; max-width: 12rem; margin: 0 auto; }
#flat path, #flat use { fill: none; stroke-width: 18; stroke-linecap: round;
                        stroke-linejoin: round; }
.r1 { stroke: var(--r1); } .r2 { stroke: var(--r2); }
.h { stroke: var(--panel); stroke-width: 48; stroke-linecap: butt; }
.c { fill: none; stroke: var(--mark); stroke-width: 7; }
#flat path.cl { stroke: var(--join); stroke-width: 10; stroke-dasharray: 26 18; }
.flatbox { background: var(--panel); border: 1px solid var(--rule); border-radius: 6px;
           padding: .5rem; }
p.note { color: var(--muted); font-size: .85rem; }
</style>
</head>
<body>
{defs}
<main>
<h1>Knot Crossings in 3D</h1>
<p class="back"><a href="https://gernreich.github.io/">&larr; All projects</a>
&middot; <a href="index.html">&larr; Knot Crossings</a></p>
<div class="lay">
<div class="stage">
<canvas id="view" aria-label="Turnable 3D view of the two ropes"></canvas>
<p class="hint">Drag to turn &middot; right-drag or shift-drag to move &middot; wheel or pinch to zoom &middot; double-click to turn round a point</p>
</div>
<div class="panel">
<div class="pick">
<button id="prev" aria-label="previous drawing">&larr;</button>
<input id="n" type="number" min="0" max="255" value="117" aria-label="drawing number">
<button id="next" aria-label="next drawing">&rarr;</button>
<button id="rand">random</button>
</div>
<fieldset><legend>Ends</legend>
<label><input type="radio" name="ends" value="loose" checked> loose</label>
<label><input type="radio" name="ends" value="own"> joined own</label>
<label><input type="radio" name="ends" value="across"> joined across</label>
</fieldset>
<fieldset><legend>Rope</legend>
<label><input type="radio" name="rope" value="plain" checked> plain</label>
<label><input type="radio" name="rope" value="laid"> laid, three strands</label>
</fieldset>
<fieldset><legend>Show</legend>
<label><input type="checkbox" id="nums"> crossing numbers</label>
<label><input type="checkbox" id="spin" checked> spin</label>
</fieldset>
<div id="info"></div>
<div class="flatbox"><svg id="flat" role="img" aria-label="the drawing, flat"></svg></div>
<p class="note">Each rope lifts toward you where it goes over and drops away where it goes under,
as the drawing&rsquo;s circles say. The 1st rope is red, the 2nd blue. Loose is the rope in the
hand. Joined own closes each rope on itself (a link) and joined across runs one rope into the
other (a knot), the two closures the main page names; the joining rope is grey.</p>
</div>
</div>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const D = {data};
const R = 17, H = 27;               // rope radius, and how far a pass lifts or drops at a crossing
const PITCH = 105;                  // length of one turn of a laid strand
const CX = 335, CY = 600;           // middle of the key
const V = (x, y, z = 0) => new THREE.Vector3(x - CX, CY - y, z);

// --- the ropes as 3D control points ------------------------------------------
const overPass = (n, k) => D.at[k][(n >> (k - 1)) & 1];
function ropePoints(n, r) {
  const overs = new Set(Object.keys(D.at).map(k => overPass(n, +k)));
  return D.ropes[r].map(([x, y, i]) => V(x, y, i < 0 ? 0 : overs.has(i) ? H : -H));
}
function bez(b, t) {
  const u = 1 - t;
  const c = [u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t];
  return [0, 1].map(j => c[0] * b[j] + c[1] * b[2 + j] + c[2] * b[4 + j] + c[3] * b[6 + j]);
}
function arc(mode, from, to) {   // points strictly between two ends, along the joining path
  for (const b of D.close[mode]) {
    const s = [b[0], b[1]], e = [b[6], b[7]];
    const same = (p, q) => p[0] === q[0] && p[1] === q[1];
    let ts = [1, 2, 3, 4, 5, 6, 7].map(i => i / 8);
    if (same(s, from) && same(e, to)) return ts.map(t => V(...bez(b, t)));
    if (same(e, from) && same(s, to)) return ts.reverse().map(t => V(...bez(b, t)));
  }
  throw new Error('no joining path');
}
// each loop: control points with a colour label (0 1st, 1 2nd, 2 join) for the span after it
function loops(n, mode) {
  const p = [ropePoints(n, 0), ropePoints(n, 1)];
  const end = r => D.ropes[r][D.ropes[r].length - 1].slice(0, 2), start = r => D.ropes[r][0].slice(0, 2);
  const lab = (pts, l) => pts.map(v => ({ v, l }));
  const rope = r => { const a = lab(p[r], r); a[a.length - 1].l = 2; return a; };
  if (mode === 'loose') return [0, 1].map(r => ({ pts: lab(p[r], r), closed: false }));
  if (mode === 'own') return [0, 1].map(r => ({ pts: rope(r).concat(lab(arc('own', end(r), start(r)), 2)), closed: true }));
  return [{ pts: rope(0).concat(lab(arc('across', end(0), start(1)), 2), rope(1),
                                 lab(arc('across', end(1), start(0)), 2)), closed: true }];
}

// Catmull-Rom through the control points, as the flat drawing does, then
// resampled at even steps along the rope
function centreline(loop, step) {
  const P = loop.pts, m = P.length, dense = [];
  const at = i => loop.closed ? P[(i + m) % m].v : P[Math.max(0, Math.min(m - 1, i))].v;
  const spans = loop.closed ? m : m - 1;
  for (let i = 0; i < spans; i++) {
    const p0 = at(i - 1), p1 = at(i), p2 = at(i + 1), p3 = at(i + 2);
    for (let s = 0; s < 32; s++) {
      const t = s / 32, t2 = t * t, t3 = t2 * t;
      const v = new THREE.Vector3();
      for (const [q, w] of [[p0, -t3 + 2 * t2 - t], [p1, 3 * t3 - 5 * t2 + 2],
                            [p2, -3 * t3 + 4 * t2 + t], [p3, t3 - t2]]) v.addScaledVector(q, w / 2);
      dense.push({ v, l: P[i].l });
    }
  }
  dense.push({ v: (loop.closed ? P[0] : P[m - 1]).v.clone(), l: P[spans - 1].l });
  const len = [0];
  for (let i = 1; i < dense.length; i++) len.push(len[i - 1] + dense[i].v.distanceTo(dense[i - 1].v));
  const L = len[len.length - 1], N = Math.max(8, Math.round(L / step)), out = [];
  for (let j = 0, i = 0; j <= N; j++) {
    const s = L * j / N;
    while (i < dense.length - 2 && len[i + 1] < s) i++;
    const f = (s - len[i]) / Math.max(1e-9, len[i + 1] - len[i]);
    out.push({ v: dense[i].v.clone().lerp(dense[i + 1].v, f), l: dense[i].l, s });
  }
  if (loop.closed) out.pop();           // the last point is the first again
  return { pts: out, L, closed: loop.closed };
}

class Polyline extends THREE.Curve {    // straight between close points, by length
  constructor(v, closed) {
    super(); this.v = closed ? v.concat([v[0]]) : v; this.len = [0];
    for (let i = 1; i < this.v.length; i++) this.len.push(this.len[i - 1] + this.v[i].distanceTo(this.v[i - 1]));
  }
  getPoint(t, out = new THREE.Vector3()) {
    const L = this.len[this.len.length - 1], s = t * L;
    let lo = 0, hi = this.len.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (this.len[mid] <= s) lo = mid; else hi = mid; }
    const f = (s - this.len[lo]) / Math.max(1e-9, this.len[hi] - this.len[lo]);
    return out.copy(this.v[lo]).lerp(this.v[hi], f);
  }
}

function colours() {
  const css = getComputedStyle(document.documentElement);
  return ['--r1', '--r2', '--join'].map(k => new THREE.Color(css.getPropertyValue(k).trim()));
}
function tube(v, labels, closed, radius, radial, shade) {
  const segs = closed ? v.length : v.length - 1;
  const g = new THREE.TubeGeometry(new Polyline(v, closed), segs, radius, radial, closed);
  const C = colours(), col = [];
  for (let i = 0; i <= segs; i++) {
    const c = C[labels[i % labels.length]].clone().multiplyScalar(shade);
    for (let j = 0; j <= radial; j++) col.push(c.r, c.g, c.b);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  return g;
}
// three strands laid round the centreline: parallel-transported frames, with
// a closed loop's leftover twist spread along it and a whole number of turns
function strands(c) {
  const P = c.pts.map(p => p.v), n = P.length, T = [], N = [];
  for (let i = 0; i < n; i++) {
    const a = c.closed ? P[(i - 1 + n) % n] : P[Math.max(0, i - 1)];
    const b = c.closed ? P[(i + 1) % n] : P[Math.min(n - 1, i + 1)];
    T.push(b.clone().sub(a).normalize());
  }
  let n0 = new THREE.Vector3(0, 0, 1).cross(T[0]);
  if (n0.length() < 1e-3) n0 = new THREE.Vector3(1, 0, 0).cross(T[0]);
  N.push(n0.normalize());
  const transport = (v, t) => v.clone().addScaledVector(t, -v.dot(t)).normalize();
  for (let i = 1; i < n; i++) N.push(transport(N[i - 1], T[i]));
  let twist = 0, pitch = PITCH;
  if (c.closed) {
    const back = transport(N[n - 1], T[0]);
    twist = Math.atan2(N[0].clone().cross(back).dot(T[0]), N[0].dot(back));
    pitch = c.L / Math.max(1, Math.round(c.L / PITCH));
  }
  const rho = 0.56 * R, out = [];
  for (let j = 0; j < 3; j++) {
    const v = [];
    for (let i = 0; i < n; i++) {
      const s = c.pts[i].s, B = T[i].clone().cross(N[i]);
      const phi = 2 * Math.PI * (s / pitch + j / 3) - twist * s / c.L;
      v.push(P[i].clone().addScaledVector(N[i], rho * Math.cos(phi)).addScaledVector(B, rho * Math.sin(phi)));
    }
    out.push(v);
  }
  return out;
}

// --- scene ---------------------------------------------------------------------
const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 4 / 3, 10, 20000);
const controls = new THREE.OrbitControls(camera, canvas);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x6f6a60, 0.7));
const sun = new THREE.DirectionalLight(0xffffff, 0.75);
sun.position.set(500, 700, 1200);
scene.add(sun);
const back = new THREE.DirectionalLight(0xffffff, 0.25);
back.position.set(-600, -300, -900);
scene.add(back);
const world = new THREE.Group();
scene.add(world);
const ropeGroup = new THREE.Group(), numGroup = new THREE.Group();
world.add(ropeGroup, numGroup);
const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.75, metalness: 0 });

function label(text) {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128;
  const x = cv.getContext('2d');
  x.fillStyle = 'rgba(255,255,255,0.85)'; x.beginPath(); x.arc(64, 64, 52, 0, 7); x.fill();
  x.fillStyle = '#1d1d1b'; x.font = 'bold 76px Georgia, serif';
  x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(text, 64, 68);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), depthTest: false }));
  s.scale.set(44, 44, 1); s.renderOrder = 2;
  return s;
}
for (const k of Object.keys(D.at)) {
  const [, , , [x, y]] = D.passes[D.at[k][0]];
  const s = label(k); s.position.copy(V(x, y, H + R + 30)); numGroup.add(s);
}

let current = 117;
const val = name => document.querySelector(`input[name=${name}]:checked`).value;
function build() {
  for (const m of ropeGroup.children) m.geometry.dispose();
  ropeGroup.clear();
  const laid = val('rope') === 'laid';
  for (const loop of loops(current, val('ends'))) {
    const c = centreline(loop, laid ? PITCH / 24 : 6);
    const labels = c.pts.map(p => p.l);
    if (laid) strands(c).forEach((v, j) =>
      ropeGroup.add(new THREE.Mesh(tube(v, labels, c.closed, 0.52 * R, 10, [1, 0.82, 0.92][j]), mat)));
    else ropeGroup.add(new THREE.Mesh(tube(c.pts.map(p => p.v), labels, c.closed, R, 16, 1), mat));
    if (!c.closed) for (const p of [c.pts[0], c.pts[c.pts.length - 1]]) {
      const g = new THREE.SphereGeometry(laid ? 1.08 * R : R, 20, 14);
      const col = [], C = colours()[p.l];
      for (let i = 0; i < g.attributes.position.count; i++) col.push(C.r, C.g, C.b);
      g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
      const m = new THREE.Mesh(g, mat); m.position.copy(p.v); ropeGroup.add(m);
    }
  }
  numGroup.visible = document.getElementById('nums').checked;
  flat();
  document.getElementById('info').innerHTML = D.info[current];
  document.getElementById('n').value = current;
  history.replaceState(null, '', '#' + current);
}

// the flat drawing, as on the main page
function flat() {
  const n = current, mode = val('ends'), parts = [];
  if (mode !== 'loose') for (const d of D.closePaths[mode]) parts.push(`<path class="cl" d="${d}"/>`);
  parts.push('<use href="#rope1"/><use href="#rope2"/>');
  for (const k of Object.keys(D.at)) {
    const [r, , [dx, dy], [x, y]] = D.passes[overPass(n, +k)], s = 42 / Math.hypot(dx, dy);
    const seg = `M${(x - dx * s).toFixed(0)} ${(y - dy * s).toFixed(0)}L${(x + dx * s).toFixed(0)} ${(y + dy * s).toFixed(0)}`;
    parts.push(`<path class="h" d="${seg}"/><path class="r${r + 1}" d="${seg}"/>`);
    if ((n >> (k - 1)) & 1) parts.push(`<circle class="c" cx="${x}" cy="${y}" r="44"/>`);
  }
  const svg = document.getElementById('flat');
  svg.setAttribute('viewBox', mode === 'loose' ? '0 110 680 960' : '-80 30 820 1110');
  svg.innerHTML = parts.join('');
}

function show(n) { current = ((Math.round(n) % 256) + 256) % 256; build(); }
document.getElementById('prev').onclick = () => show(current - 1);
document.getElementById('next').onclick = () => show(current + 1);
document.getElementById('rand').onclick = () => show(Math.floor(Math.random() * 256));
document.getElementById('n').addEventListener('change', e => { if (e.target.value !== '') show(+e.target.value); });
document.querySelectorAll('input[name=ends], input[name=rope], #nums').forEach(e => e.addEventListener('change', build));
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', build);
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' && e.target.type === 'number') return;
  if (e.key === 'ArrowLeft') show(current - 1);
  if (e.key === 'ArrowRight') show(current + 1);
});
window.addEventListener('hashchange', () => { const h = parseInt(location.hash.slice(1)); if (h >= 0 && h < 256 && h !== current) show(h); });

// --- turning, moving and zooming ----------------------------------------------
const spin = document.getElementById('spin');
const home = new THREE.Vector3(0, -260, 1850);
camera.position.copy(home);
controls.target.set(0, 0, 0);
controls.enableZoom = false;
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
function under(cx, cy, ropeOnly) {   // the rope under the pointer, else where the ray meets the plane through the target
  const b = canvas.getBoundingClientRect();
  ndc.set((cx - b.left) / b.width * 2 - 1, -(cy - b.top) / b.height * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObject(ropeGroup, true)[0];
  if (hit || ropeOnly) return hit ? hit.point : null;
  const nrm = camera.getWorldDirection(new THREE.Vector3());
  return ray.ray.intersectPlane(new THREE.Plane().setFromNormalAndCoplanarPoint(nrm, controls.target), new THREE.Vector3());
}
function zoom(s, cx, cy) {   // scale the view about the point under the pointer
  const d = camera.position.distanceTo(controls.target), k = Math.max(80, Math.min(6000, d * s)) / d;
  const p = under(cx, cy) || controls.target.clone();
  camera.position.sub(p).multiplyScalar(k).add(p);
  controls.target.sub(p).multiplyScalar(k).add(p);
}
canvas.addEventListener('wheel', e => { e.preventDefault(); spin.checked = false; zoom(1 + Math.sign(e.deltaY) * 0.08, e.clientX, e.clientY); }, { passive: false });
let pinch = 0;
const gap = t => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
canvas.addEventListener('touchstart', e => { pinch = e.touches.length === 2 ? gap(e.touches) : 0; });
canvas.addEventListener('touchmove', e => {
  if (e.touches.length !== 2 || !pinch) return;
  const g = gap(e.touches);
  if (g) zoom(pinch / g, (e.touches[0].clientX + e.touches[1].clientX) / 2, (e.touches[0].clientY + e.touches[1].clientY) / 2);
  pinch = g;
});
canvas.addEventListener('touchend', () => { pinch = 0; });
const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function glide(target, cam) {
  const t0 = controls.target.clone(), c0 = camera.position.clone(), start = performance.now();
  const step = t => { const k = still ? 1 : Math.min(1, (t - start) / 300), e = k * (2 - k);
    controls.target.lerpVectors(t0, target, e); camera.position.lerpVectors(c0, cam, e);
    if (k < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}
canvas.addEventListener('dblclick', e => {
  spin.checked = false;
  const p = under(e.clientX, e.clientY, true);
  if (p) { glide(p, camera.position.clone().add(p).sub(controls.target)); return; }
  world.rotation.set(0, 0, 0);
  glide(new THREE.Vector3(), home.clone());     // empty space: back to the opening view
});
if (still) spin.checked = false;
controls.addEventListener('start', () => { spin.checked = false; });
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== Math.round(w * renderer.getPixelRatio())) {
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
}
const h0 = parseInt(location.hash.slice(1));
show(h0 >= 0 && h0 < 256 ? h0 : 117);
(function loop() {
  resize();
  if (spin.checked) world.rotation.y += 0.004;
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(loop);
})();
</script>
</body>
</html>
"""


def outputs():
    group_of, members, mirror, names, drawn = analyse()
    results = {
        "knots.txt": knots_txt(group_of, mirror, names, drawn).encode(),
        "groups.txt": groups_txt(members, mirror, names, drawn).encode(),
        "checks.txt": checks_txt(group_of, members, mirror, names).encode(),
        "closures.txt": closures_txt(names, group_of).encode(),
    }
    files = {f"results/{name}": data for name, data in results.items()}
    files["index.html"] = page(group_of, members, mirror, names, drawn, results)
    files["turn.html"] = turn_page(group_of, names, drawn)
    return files


def main():
    check = "--check" in sys.argv[1:]
    changed = []
    RESULTS.mkdir(exist_ok=True)
    for name, data in outputs().items():
        path = HERE / name
        if path.exists() and path.read_bytes() == data:
            continue
        changed.append(name)
        if not check:
            path.write_bytes(data)
    if check:
        for name in changed:
            print(f"{name} is out of date; run python3 knot_crossings.py")
        sys.exit(1 if changed else 0)
    for name in changed:
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
