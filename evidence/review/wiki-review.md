# Wiki review (all 27 notes), done with Claude's help

**Who did what:** I found the first error (Group Pricing) myself while reading the note in Obsidian. The systematic check below (all 27 notes, all 153 key points) was done by Claude, an AI assistant, at my request. I did not run `wiki approve`, so all notes keep `status: draft`.

## Method
1. **Structure (automatic, also a unit test):** each note's first heading equals its file name; every `[[link]]` resolves to an existing note or original; no self-links; every note has 1-4 related notes; every original is cited by at least one note. Result: all 27 pass.
2. **Grounding of every key point (automatic):** for all **153 key points**, the words of the point were compared with the passages its own source link points to
   (`evals/fix_misattributed_links.py`). Average coverage 0.99: nearly every word of nearly every key point is in the passage it cites.
3. **Reading the low-coverage points against the raw files (manual, by Claude):** five points scored below 0.85; each was read against `vault/raw/`.

## Findings
| # | Note | Finding | Kind | Action |
|---|---|---|---|---|
| 1 | Group Pricing | arbitrage / "senior discount" point cited my Netflix document; it is a lecture sentence. Two key points about menu pricing were off-topic | wrong source, off-topic | corrected (details: [group-pricing-review.md](group-pricing-review.md)) |
| 2 | A-B Testing | "Randomization eliminates confounding factors..." is true but linked to Lecture 10; it is in **Lecture 6** (line 250) | right claim, wrong section link | link, Sources list and properties repaired |
| 3 | Linear Regression | "R squared measures the fraction of variation..." linked to Lecture 7; it is in **Lecture 9** (line 399) | same | repaired |
| 4 | Control Limits | "The sample average is Normal if..." linked to Lecture 1; it is in **Lecture 4** (line 135) | same | repaired |
| 5 | Two-Part Tariffs | "With MC = 0, P = 0 and F = $200 creates and captures all the value" linked to Lecture 6; it is in **Lecture 5** | same | repaired |
| 6 | Hypothesis Testing | related link to Decision Trees; the model's own reason says "No clear connection" | weak link | **left unfixed** (my decision) |
| 7 | Cost Disease | related link to Omitted Variable Bias; reason is a stretch | weak link | **left unfixed** |

So **5 of 153 key points (3%) had a wrong source reference** (one of them a wrong document), all with a claim that is otherwise supported by the sources; none invented a fact.
The originals in `raw/` were never edited. The versions of the four repaired notes exactly as generated are in [as-generated/](as-generated).

## What this review did NOT check
* Whether each "related notes" reason is convincing (only that the target exists); the two weak ones above were noticed, others may exist.
* Whether the summaries at the top of each note are complete; only their numbers/words were compared with the sources indirectly.
* The lecture summaries in `raw/` against the original slides (I spot-checked 8 items myself: see `lecture-summary-spot-check.md`).

## Why the harness did not catch the wrong section links
Ingest accepts a key point when its cited label exists and its figures appear in that passage; it does not test that the *words* of the point are in the passage the link
names. This review's grounding script does exactly that and could be built into ingest (see the README's improvement ideas).
