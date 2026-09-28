# Choices and expectations (written 2026-09-27, before search, ask or chat existed)

This file records what I chose and what I expect. Results are compared with it later; it is never edited to match the results.
If a setting changes after a failure, the change is documented in a new section below and the earlier result is kept.

## Data: what the wiki is for
A personal study wiki for my Berkeley Haas MBA Fall A courses (MBA 201A Economics, MBA 200S Data & Decisions), used offline for
revision: "what did the lecture say about X, and where?"

Ten sources in `vault/raw/`, all shareable:
- `Economics Lectures.md` and `Data and Decisions Lectures.md`: my own-words summaries of the 19 lecture slide decks (9 + 10 lectures),
  written with Claude's help from the slides; the slides themselves are not published. One `## Lecture N: title` section per lecture.
- Eight of my own Word documents, unchanged: Sunk Cost Reasoning, Relevant Cost, Supply and Demand Shocks, Group Pricing, Menu Pricing,
  Durable Advantage (Examples in the Wild) and AuraTech Case, Uber Case (case questions).

Questions the wiki should answer: definitions, rules and worked numbers from the lectures, and how my own examples apply them.
Questions it should NOT answer: anything about the courses that is not in these sources (exam dates, instructors' opinions, the textbook).

## Model
`gemma4:e2b`, Q4_K_M (5.1B parameters including embedding tables, 7.2 GB file) through Ollama 0.34.3 on CPU.
Device: Snapdragon X Plus (8-core ARM64), 15.6 GB RAM, no dedicated GPU.
Why: the smallest Gemma size offered; measured 6.7 GB in memory at a 4,096-token context and ~22.7 tokens/s (see
`evidence/baseline-measurements.md`). A 26B model would not fit; E4B would leave too little memory next to other apps.
Settings I expect to matter: thinking off (`think=false`) for speed and clean output, low temperature for ask, a context window of 8,192.

## Retrieval
SQLite FTS5 keyword search (BM25 ranking), no embeddings. Passages of up to 1,200 characters, split at headings and paragraphs, each keeping
file name, lecture/section and line range (120 passages for the current sources). Ask retrieves the top 5 passages.
Text sent to Gemma in ask: at most 5 x 1,200 characters (about 1,500 tokens) plus about 300 tokens of instructions.

## Predictions for the four tests
| Test | Retrieval prediction | Answer prediction |
|---|---|---|
| 1. Poll sample size | Easy: "margin of error", "percentage points", "poll" are distinctive words in one passage of Data Lecture 5. Expect it at rank 1-2. | Correct: 1,112 people, cited to Data Lecture 5. |
| 2. Monopolist and price = marginal cost | Harder: the source says "price maker", "MR = MC", "golden rule", not "keep producing". Keyword search may rank Economics Lecture 3 (price-taker rule) above or beside Lecture 5. I expect Lecture 5 in the top 5 but not certain. | Should explain marginal revenue < price. Risk: mixes in Lecture 3 (price taker) wording. |
| 3. Group pricing conditions + Netflix | Needs two sources. "group pricing" and "Netflix" are distinctive, so I expect both Lecture 6 and `Group Pricing.docx` in the top 5. Risk: one of them is pushed out by other price-discrimination passages (Lecture 7). | Should list identify / separate / prevent arbitrage and map Netflix onto them, citing both sources. |
| 4. Final exam date | Retrieval will still return passages ("final exam" appears in both logistics sections with grade weights), which is the trap. | Expected: "insufficient evidence". Risk: the model quotes the 20% / 40% weights as if they answered, or invents a date. If it does, that is a failure to record, with the fix documented. |

## Expected timing
Ask response: about 10-20 s (prompt of ~2,000 tokens on CPU plus a short answer). Ingestion of the 10 sources: to be measured.

---
## Addendum, 2026-09-28: changes made after these expectations were written (results are NOT edited into the sections above)
- **Sources:** the Uber case document was removed from `vault/raw/` before publishing because its last line contained a local file path with the
  student's Windows user name. The wiki now has 9 sources (2 lecture summaries + 7 own documents), 114 passages (was 120) and 27 notes.
  The retrieval predictions above were written for the 10-source index; the four tests were rerun on the final index (`evidence/ask-tests/run-6-final-index`).
- **Timing prediction was wrong:** "10-20 s per ask answer" assumed a cached prompt. Measured cold/novel questions take 105-120 s end to end on this
  machine with other apps open (answer about 80 s, verification 24-35 s). See the README.
- **Design changes after failures** (each documented with before/after evidence): instruction versions 1-3 (`evidence/ask-tests`), a draft verification step,
  a draft-free answerability check for fact-seeking questions, evidence-based link candidates for wiki notes (`evidence/ingest`), and a persona/harness
  change for capability questions in chat (`evidence/mode-checks`).
