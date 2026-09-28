# Wiki review checklist

The assignment says generated notes must be **reviewed against the originals**, and that mistakes are corrected in the wiki (never in `raw/`).
Open `vault/` as the vault in Obsidian. Work through the 27 notes; after checking a note, run `wiki approve "<Title>"` (or `wiki approve --all` when done).

For each note, spend two minutes on:
1. **Heading and file name match**, and the name is readable in the file list and the graph.
2. **Summary** (top paragraph): true according to the sources? Anything that sounds invented or too general?
3. **Key points**: click the source link next to 2 points. Does the cited lecture section / document really say it? Are the numbers exact?
4. **Related notes**: is each reason true and useful? Delete weak or silly links (for example a link justified only by a shared word). Add an obvious missing link by hand.
5. **Sources section**: does every listed source exist and open?

Known weak spots to look at first:
- "Related notes" reasons are written by Gemma and checked only for existence, not for meaning (Menu Pricing -> Option Value is an example of a shaky one).
- `Cost Disease` and `Menu Pricing` have no incoming links from other notes (only from the index).
- Notes whose key points repeat each other; notes that mix in a neighbouring topic (Group Pricing also describes menu pricing).
- Lecture-summary sources were written by Claude from the slides: if a key point is wrong, check the lecture summary in `vault/raw/` against your slides too.

Spot-check the lecture summaries (they are the evidence!): Economics L5 (bakery: 4 batches at $25, profit $24; County Fair $24 and $128), L7 (coffee: Nice $2, Super $4.50, profit $4.10),
L9 (Merck: launch A now $2.85; wait $2.97-$3.27); Data L5 (turbine test t = -1.6949, p = 0.04961), L7 (diamonds slope 2,697, intercept 15, R-squared 0.509),
L9 (coffee shop regression -123.43 + 10.09 Income - 27.62 Competitors). Two places to look at first: Economics L6 (my arithmetic on the two-part tariff profit) and Data L8 (the "143.36 + 143.31 x 50" line).

Obsidian screenshots to take (README needs them): (1) an open note showing its heading, key points with source links, related notes and Sources;
(2) `index.md` (or the file explorer showing the topic folders); (3) the graph view with the filter `path:wiki/` and Attachments turned off, zoomed until labels are readable.
Also click one link from a note to a related note and back to its original in `raw/` (and check `Source Catalog.md`).

**Update 2026-09-28:** the spot-check of the lecture summaries was done by me and all items matched (see evidence/review/lecture-summary-spot-check.md).
