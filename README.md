# Knot Crossings

**[← All projects](https://gernreich.github.io/)**

Two ropes, drawn once and crossing each other 8 times. Every crossing can go
either way, over or under, so the one drawing holds 2⁸ = 256 knots. The author
drew all 256 by hand on yellow legal paper, numbered 0 to 255, and marked each
crossing that goes the other way with a small circle. The circles are the
number written in binary: crossing 1 is the units digit, crossing 2 the twos,
crossing 3 the fours, up to crossing 8 for 128. The knots the author
recognised are listed in an index: the square knot, the sheet bend, the
Carrick bend and its relatives.

**[See all 256](https://gernreich.github.io/knot-crossings/)**: the key, the
index checked, the groups, and every drawing redrawn with its crossings.

## The key

On the key, one rope starts at the circle marked "1st" (bottom right) and
leaves by the arrow at the bottom left. On the way it passes crossings
8, 6, 4, 1, 2, 5, 6, 7. The other starts at "2nd" (top left) and leaves by
the arrow at the top right, passing 1, 3, 5, 8, 7, 4, 3, 2. Each rope crosses
itself once and the other rope six times, as in a Carrick bend.

The drawings show only which crossings are circled, not which rope is on top.
`knot_crossings.py` reads them this way: without a circle, a crossing goes over
for the rope that reaches it first, following the 1st rope and then the 2nd. A
circle turns that crossing the other way. Under this reading, 117, the
drawing the index calls "The Carrack bend", and its mirror image
138 = 255 − 117 are the only two that go over, under, over, under all the way
along both ropes, as the Carrick bend does. Reading every crossing the
other way would give the mirror image of every drawing and change no name.

## The index, checked

Each drawing is sorted by its Kauffman bracket, taken with the four ends held,
and two drawings count as one knot when they differ only by a rope's two ends
being turned about each other, as they can be in the hand. Different brackets
prove different knots; the same bracket strongly suggests, but does not prove,
the same knot. The 256 drawings fall into 20 groups.

| Index name | Drawings | Groups |
|---|---|---|
| square knot | 24, 28, 56, 60, 98, 122 | one group, its own mirror image (as the square knot is) |
| sheet bend | 26, 29, 58, 61, 99, 103, 120 | a group and its mirror image |
| single carrick bend (reformed constrictor) | 77, 105, 109 | two different groups |
| single carrick bend (unknown) | 74, 106 | two different groups |
| single carrick bend | 114 | one group |
| The Carrick bend | 117 | one group; alternating, like its mirror image 138 |
| Carrick bend (unknown) | 118 | one group |
| whatnot | 73, 101 | two different groups |

- **Nothing missed.** No drawing up to 122, the last one indexed, is in a
  named group without being named.
- **Three pairs of names are mirror images.** 74 (single carrick, unknown) and
  118 (carrick, unknown); 106 (single carrick, unknown) and 114 (single
  carrick); and 73 (whatnot, its first name covered with correction fluid) and
  109 (single carrick, reformed constrictor).
- **The reformed constrictor is two knots.** 77 and 105 are one knot, which is
  its own mirror image; 109 is another, whose mirror image is 73.
- **"Overhand" is two kinds.** Written beside drawings 1 and 5, it marks the
  ropes wound once round each other; beside 9, 13 and 18, twice.

`results/checks.txt` holds the full comparison, `results/groups.txt` every
group, and `results/knots.txt` every drawing.

## Closing the ends

A rope with loose ends can always be untied, so to ask whether a drawing is
really knotted its four ends have to be joined. They lie round the outside of
the drawing, and two ways of joining them add no crossing: each rope's end
back to its own start (two loops, a link), or each rope's end on to the other
rope's start (one loop, a knot). `knot_crossings.py` closes every drawing
both ways and names what comes out by its Jones polynomial, which differs
between every knot and link that turns up. It also works out the Alexander
polynomial from the Wirtinger presentation, and the two must agree on the
determinant, |Δ(−1)| = |V(−1)|. They agree for all 512. Every name was also
checked with SnapPy, which is not needed to run the script.

| Own ends joined | Drawings | | Ends joined across | Drawings |
|---|---:|---|---|---:|
| unlink | 56 | | unknot | 88 |
| Hopf link (L2a1) | 110 | | trefoil 3₁, either hand | 72 |
| Solomon link (L4a1) | 44 | | 5₂, either hand | 32 |
| Whitehead link (L5a1) | 24 | | 5₁, either hand | 16 |
| L6a1, L6a2, L6a3, L7a5, L7a6 | 4 each | | 6₃ | 16 |
| L8a8 | 2 | | 8₂₀, either hand | 16 |
| | | | square knot 3₁ # 3₁* | 8 |
| | | | figure-eight 4₁ | 4 |
| | | | 8₁₈, the Carrick mat | 2 |
| | | | 8₁₉, the (3,4) torus knot, either hand | 2 |

- **The Carrick bend closes to the Carrick mat.** 117 joined across is
  8₁₈, the 3-lead 4-bight Turk's head; joined on itself it is the link L8a8.
  Only 117 and its mirror image 138 reach 8 crossings in both closures.
- **The square knot comes apart, the sheet bend does not.** Every square knot
  in the index gives two unlinked loops when each rope is closed on itself;
  every sheet bend gives a Hopf link.
- **One name, different closures.** An index name belongs to the knot in the
  hand, with its ends free to turn, but a closure depends on how the ends lie.
  Square knots 28, 56, 98 and 122 close across to the square knot, but 24 and
  60 close to 8₂₀. 8₂₀ has the same Alexander polynomial and determinant as the
  square knot, and only the Jones polynomial tells them apart.
- **The reformed constrictor again.** 77 and 105 close to L6a2 and 5₁, and
  109 to L6a3 and the trefoil, a second sign that the one name covers two
  knots.

`results/closures.txt` lists every knot and link with its polynomials and
drawings, and every named drawing's two closures. `results/knots.txt` gives
both for every drawing.

## What is here

| Path | Contents |
|---|---|
| `scans/knot-crossings.pdf` | the four sheets, front and back, with the scanner's metadata removed |
| `original/index.txt` | the index (scan page 1), transcribed |
| `original/drawings.txt` | what is written and marked beside the drawings (scan pages 3, 5 and 7) |
| `knot_crossings.py` | the key traced, all 256 worked out, and the page drawn |
| `results/` | the tables it writes |
| `index.html` | the page it writes |

```
python3 knot_crossings.py           # writes results/ and index.html
python3 knot_crossings.py --check   # exits 1 if any of them would change
```

It needs only the Python standard library.

## Transcription notes

- The scan has eight pages: the index, the drawings 0 to 83, 84 to 203 and
  204 to 255, each followed by the back of its sheet. The backs show only ink
  coming through, apart from "700" circled in orange on the last.
- Two numbers in the index read oddly: the line after 101 looks like "10)"
  and the line after that like "165". The list runs in order, and the
  drawings agree: they are 103 and 105.
- "Carrick" is spelled "carrick" and "carrack" in turn. In the transcription
  each is kept as written, and the program counts them as one word.
- The name first given to 73 is covered with correction fluid, and "whatnot"
  is written after it. In line 99 a "Sq" is struck through before "Sheet bend".
- The drawing pages are upside down in the scan, and every
  drawing is redrawn freehand, so the shapes vary from drawing to drawing; the
  crossings are always the key's.
