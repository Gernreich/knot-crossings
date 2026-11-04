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

| Index name | Drawings | Groups | In Ashley |
|---|---|---|---|
| square knot | 24, 28, 56, 60, 98, 122 | one group, its own mirror image (as the square knot is) | Reef Knot, #1402; Thief Knot, #1207, with the other lead |
| sheet bend | 26, 29, 58, 61, 99, 103, 120 | a group and its mirror image | Sheet Bend, #1431 |
| single carrick bend (reformed constrictor) | 77, 105, 109 | two different groups; 109 resolved to whatnot | Single Carrick Bend, #1445 (77, 105) |
| single carrick bend (unknown) | 74, 106 | two different groups | Single Carrick Bend, #1443 or #1444 |
| single carrick bend | 114 | one group | Single Carrick Bend, #1443 or #1444 |
| The Carrick bend | 117 | one group; alternating, like its mirror image 138 | Carrick Bend, #1439 |
| Carrick bend (unknown) | 118 | one group; resolved to single carrick bend | Single Carrick Bend, #1443 or #1444 (mirror of 74) |
| whatnot | 73, 101 | two different groups | Whatnot, #1406 or #1407; Granny Knot, #1405, with the other lead |

*The Ashley Book of Knots* (1944) works from the same diagram: Ashley draws
the reef knot, sheet bend, Carrick bend and granny knot on it (#1549–1552)
and notes the 256 over-and-under arrangements an eight-crossing knot allows.
In 2025 Eric (NautiKnots on the International Guild of Knot Tyers forum)
tied every one, with the standing ends on the same side and on opposite
sides, and named each bend that held from Ashley:
[Bends Based on the Carrick Bend Diagram](https://discourse.igkt.net/t/bends-based-on-the-carrick-bend-diagram/6260).
The "In Ashley" column and the names below are matched to these drawings from
that thread. "Reformed constrictor" is not Ashley's name.

Eric's crossings A–H are crossings 6, 1, 5, 8, 7, 4, 3, 2 of the key. The
figures of the Thief Knot (#1207), the Carrick Bend (#1439) and the third
Single Carrick Bend (#1445), read crossing by crossing, come out as drawings
195/199/227/231, 138 and 117, and 178 and 77, each in the group already found
for it. The other figures no longer load, so the rest are matched by
elimination from Eric's counts (three Single Carrick Bends, two Whatnots, the
Whatnot tied 8 ways, the Thief Knot 12). The total agrees too: 100 of the 512
bends held, and groups 1–6 here hold 206 drawings, leaving 50 knotted
drawings, 100 with both leads. Moving a standing end changes how the knot is
pulled, not the drawing, so one drawing can carry a name for each lead:

| Groups | Ashley | Other names (credit) |
|---|---|---|
| 7 (square knot) | Reef Knot, #1402 | Thief Knot, #1207, ends on opposite sides (Eric) |
| 8, 9 (sheet bend) | Sheet Bend, #1431 | Left-Hand Sheet Bend, #1432, the bight's lead reversed, the same knot and not the other hand (Eric); with the other lead reversed, Eskimo Sheet Bend (Eric) or Lapp Bend (knotsaver) |
| 17, 20 (117, 138) | Carrick Bend, #1439; Ashley's figure is 138 (Eric) | #1428, the Double Coin Knot, or Pretzel Knot, #2283, with a lead reversed (Eric) |
| 12 (77, 105) | Single Carrick Bend, #1445; Ashley's figure is 178 (Eric) | |
| 11, 18 (74, 118) and 14, 16 (106, 114) | Single Carrick Bend, #1443 and #1444, which is which unknown | |
| 10, 15 (73, 109) and 13, 19 (101) | Whatnot, #1406 and #1407 | Granny Knot, #1405, ends on the same side (Eric) |

Every one of the 50 knotted drawings now has its Ashley number for each
lead, standing ends on the same side / on opposite sides, in
`results/knots.txt` and under each drawing on the page: for example 1402 /
1207 (reef / thief), 1405 / 1406 or 1407 (granny / whatnot), and 117 as
1428 / 1439m. Eric's suffixes: m is the mirror image of Ashley's figure, r
the lead reversed. Of Ashley's own figures, only #1439 (138) and #1445
(178) can be read from Eric's drawings. Two numbers stay open until Ashley's
figures can be read: which Single Carrick group is #1443 and which #1444, and
which Whatnot is #1406 and which #1407 (they differ by one crossing: 109
becomes 101 by changing crossing 4, as Eric's note on the two suggests).

This is what resolves the two clashes above: 109 matches as a Whatnot, the
mirror image of 73, and 118 as a Single Carrick Bend, the mirror image of 74.

- **Nothing missed.** No drawing up to 122, the last one indexed, is in a
  named group without being named.
- **Three pairs of names are mirror images.** 74 (single carrick, unknown) and
  118 (carrick, unknown); 106 (single carrick, unknown) and 114 (single
  carrick); and 73 (whatnot, its first name covered with correction fluid) and
  109 (single carrick, reformed constrictor).
- **Two clashes, resolved.** A mirror image keeps its name, so two of those
  pairs cannot both be right. 109, a single carrick bend (reformed
  constrictor) in the index, is the mirror image of 73, a whatnot; 118, a
  Carrick bend, is the mirror image of 74, a single carrick bend. Ashley's
  names (below) settle both: 109 is a whatnot (Ashley's Whatnot) and 118 a
  single carrick bend; the Carrick Bend is only 117 and its mirror 138. Read
  that way, the reformed constrictor is one knot, 77 and 105, its own mirror
  image, and no two mirror images carry the names of different knots (106
  and 114 differ only by "unknown"). `original/index.txt`
  keeps the names as written; `results/checks.txt` lists both readings.
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
- **The clash at 109 again.** 77 and 105 close to L6a2 and 5₁; 109 closes
  to L6a3, the same link as the whatnot 73, a second sign that 109 belongs
  with 73.

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

## Credits

The drawings are Michael Gernreich's; [Claude](https://www.anthropic.com/claude) (Anthropic), working in Claude Code, co-wrote the transcriptions, the code and the documentation that present them. Commits Claude made carry a `Co-Authored-By: Claude` line.
