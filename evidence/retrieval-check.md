# Retrieval check (search only, no language model)

Run 2026-09-27 with `wiki index` then `wiki search "<question>" --limit 5`, before any ask/chat code existed.
Mode: local index (SQLite FTS5, BM25), 120 passages from 10 sources. Predictions were written earlier in
`evals/choices-and-expectations.md`; the answer key is `evals/questions.toml`.

| Test | Expected evidence | Retrieved (top 5) | Verdict |
|---|---|---|---|
| 1. Poll sample size | Data and Decisions Lectures, Lecture 5 (contains "1,112 people") | Rank 1: `Data and Decisions Lectures.md#21`, Lecture 5, contains "1,112" | Hit, rank 1 (prediction: rank 1-2) |
| 2. Monopolist vs price = MC | Economics Lectures, Lecture 5 (marginal revenue below price; MR = MC) | Ranks 1-2 and 5 are Lecture 3 (price-taker rule). Rank 4: `Economics Lectures.md#20`, Lecture 5, contains "marginal revenue", "MR < P", "MR = MC" | Partial: the needed passage is in the top 5 but ranked below two price-taker passages (prediction: "in top 5, not certain"). The lecture's separate "why 6 batches is wrong" passage was NOT retrieved (not in the top 15). |
| 3. Group pricing + Netflix | Economics Lectures, Lecture 6 + `Group Pricing.docx` | Rank 1: `Group Pricing.docx#1`; rank 2: Lecture 6 passage containing "prevent arbitrage"; rank 3: `Group Pricing.docx#2` | Hit for both sources (prediction: both in top 5) |
| 4. Final exam date (unsupported) | Nothing (only the exam's weight is in the sources) | Ranks 2-3: logistics passages containing "final exam" (weights 40% / 20%), rank 1: the Economics file's intro paragraph (matched "MBA 201A") | As predicted, retrieval returns related passages that contain no date. The ask-mode test must show the model does not invent one. |

## What this means for the ask tests
- Retrieval is good enough to proceed: every answerable test has its needed passage in the top 5.
- Known weakness to watch in test 2: keyword search ranks by shared words, so "price equals marginal cost" pulls in the price-taker
  lecture. If the answer to test 2 is poor, the first fix to try is retrieval (for example a larger top-k or a query that keeps
  "monopolist"), not the prompt.
- Test 4 depends entirely on the ask-mode rules: retrieval cannot say "not found", only the harness/model can.
