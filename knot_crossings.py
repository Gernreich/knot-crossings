#!/usr/bin/env python3
"""Every way to cross two ropes at the 8 crossings of the hand-drawn key,
worked out again and checked against the hand-made index. The drawings and
the index are kept unchanged in scans/ and original/.

    python3 knot_crossings.py           # writes results/ and index.html
    python3 knot_crossings.py --check   # exits 1 if any of them would change

Standard library only.

  results/knots.txt    all 256 drawings: crossings circled, over and under
                       along each rope, linking number, group, name given
  results/groups.txt   the drawings grouped into knots
  results/checks.txt   the index set beside the groups
"""
import math
import re
import sys
from collections import defaultdict
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


def bracket(n):
    """Kauffman bracket of the drawing as a tangle with its four ends held:
    f <ends of each rope joined> + g <ends joined across>, unnormalised."""
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
             "",
             f"{'n':>3}  {'circled':<15}  {'1st rope':<8}  {'2nd rope':<8}  {'lk':>2}  "
             f"{'group':>5}  name on the page",
             ""]
    for n in range(256):
        circled = ",".join(str(k) for k in CROSSINGS if n >> (k - 1) & 1) or "-"
        w1, w2 = words(n)
        name = names.get(n) or (f'"{drawn[n]}" (on the drawing)' if n in drawn else "")
        lines.append(f"{n:>3}  {circled:<15}  {w1:<8}  {w2:<8}  {linking(n):>2}  "
                     f"{group_of[n]:>5}  {name}".rstrip())
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
    cards = []
    for n in range(256):
        label = names.get(n) or (f"&ldquo;{escape(drawn[n])}&rdquo;" if n in drawn else "")
        cards.append(f'<figure id="d{n}"{" class=named" if n in names else ""}>'
                     f'{drawing(n)}<figcaption><b>{n}</b> '
                     f'<a href="#g{group_of[n]}">g{group_of[n]}</a>'
                     f'<span>{escape(label) if n in names else label}</span>'
                     f'</figcaption></figure>')
    return (PAGE.replace("{defs}", DEFS).replace("{key}", key_drawing())
            .replace("{checks}", f"<pre>{escape(results['checks.txt'].decode())}</pre>")
            .replace("{groups}", "\n".join(rows))
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
</style>
</head>
<body>
{defs}
<main>
<h1>Knot Crossings</h1>
<p class="back"><a href="https://gernreich.github.io/">&larr; All projects</a></p>

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
<p>Every name in the hand-made index lands in a single group, or in a group
and its mirror image; the square knot, which is its own mirror image, lands in
a group that is its own mirror. No drawing up to 122, the last one indexed, is
in a named group without being named. Three pairs of names turn out to be
mirror images of one another, and one name, the reformed constrictor, covers
two different knots.</p>
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

<h2>All 256</h2>
<p>Drawn from the key, with the crossings the author circled ringed in yellow
and the drawings named in the index outlined. The two ropes keep their colours: the 1st in
red, the 2nd in blue. The originals are in <a href="scans/knot-crossings.pdf">the
scan</a>; the index and the notes beside the drawings are transcribed in
<a href="original/index.txt">original/index.txt</a> and
<a href="original/drawings.txt">original/drawings.txt</a>.</p>
<div class="grid">
{cards}
</div>
</main>
</body>
</html>
"""


def outputs():
    group_of, members, mirror, names, drawn = analyse()
    results = {
        "knots.txt": knots_txt(group_of, mirror, names, drawn).encode(),
        "groups.txt": groups_txt(members, mirror, names, drawn).encode(),
        "checks.txt": checks_txt(group_of, members, mirror, names).encode(),
    }
    files = {f"results/{name}": data for name, data in results.items()}
    files["index.html"] = page(group_of, members, mirror, names, drawn, results)
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
