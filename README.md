# Personal Wiki: a local Gemma + RAG command-line tool

`wiki` is a command-line tool and harness that lets me talk to my own MBA study material with a small open-weight model
(**Gemma `gemma4:e2b`, Q4_K_M**) that runs entirely on my laptop, offline. It has five commands:

| Command | What it does | Uses Gemma? |
|---|---|---|
| `wiki ingest` | reads `vault/raw/`, has Gemma write 27 linked wiki notes, regenerates `index.md` and the source catalog | yes |
| `wiki search "words"` | prints the original matching passages with their source and location | **no** (works with Ollama stopped) |
| `wiki ask "question"` | a neutral, standalone answer with checked citations, or "insufficient evidence" | yes |
| `wiki chat` | Scout, a study assistant with a personality, conversation memory, and notes lookups only when needed | yes |
| `wiki approve` | marks notes I have reviewed, so re-ingesting never overwrites them | no |

This is Assignment 4 (Class 5), a standalone project. **Everything below was measured on the machine described in [Setup](#setup-and-device);
where a result was bad, the README says so.**

## Where to find things (grading entry points)
| Requirement | Where |
|---|---|
| CLI and harness code | [`src/wiki/`](src/wiki) (2,200 lines, 19 modules), tests in [`tests/`](tests) (321 tests) |
| Instructions and personality (explicit files) | [`prompts/persona.md`](prompts/persona.md) (chat), [`prompts/wiki-instructions.md`](prompts/wiki-instructions.md) (ask), [`prompts/verify-instructions.md`](prompts/verify-instructions.md), [`prompts/answerable-instructions.md`](prompts/answerable-instructions.md), [`prompts/ingest-instructions.md`](prompts/ingest-instructions.md) |
| Originals (unchanged) | [`vault/raw/`](vault/raw), fingerprints in [`vault/Source Catalog.md`](vault/Source%20Catalog.md) |
| Wiki (open `vault/` in Obsidian) | [`vault/index.md`](vault/index.md), [`vault/wiki/`](vault/wiki) |
| Choices and predictions written **before** testing | [`evals/choices-and-expectations.md`](evals/choices-and-expectations.md), answer key [`evals/questions.toml`](evals/questions.toml) (outside the vault) |
| Four ask-mode tests: cards, failures, fixes | [`evidence/ask-tests/README.md`](evidence/ask-tests/README.md) (final run: [`run-6-final-index`](evidence/ask-tests/run-6-final-index/summary.md)) |
| Retrieval checked before the model | [`evidence/retrieval-check.md`](evidence/retrieval-check.md) |
| Chat / search / boundary checks | [`evidence/mode-checks/README.md`](evidence/mode-checks/README.md) |
| Ingestion timings, memory, re-ingest | [`evidence/ingest/README.md`](evidence/ingest/README.md) |
| Device and first measurements | [`evidence/baseline-measurements.md`](evidence/baseline-measurements.md) |
| Re-ingestion without duplicates (a source is changed: only its note is regenerated) | [`evidence/ingest/reingest-demo.txt`](evidence/ingest/reingest-demo.txt) |
| Search works with the model server stopped | [`evidence/mode-checks/search-without-model.txt`](evidence/mode-checks/search-without-model.txt) |
| Extraction quality of the Word files | [`evidence/extraction-check.md`](evidence/extraction-check.md) |
| Requirement-by-requirement audit against the assignment | [`evidence/requirements-audit.md`](evidence/requirements-audit.md) |
| Offline demonstration | recording [`evidence/recording/Offline recording.mp4`](evidence/recording/Offline%20recording.mp4) (29 s, condensed; see its [README](evidence/recording/README.md)), script [`demo/offline-demo.ps1`](demo/offline-demo.ps1), full transcripts in [`evidence/offline-demo/`](evidence/offline-demo) |
| Obsidian screenshots | [`evidence/screenshots/`](evidence/screenshots) (see [below](#obsidian-screenshots)) |

## Purpose and sources
A personal study wiki for two Berkeley Haas MBA Fall A courses (MBA 201A microeconomics, MBA 200S Data & Decisions) that I can question offline
("what did the lecture say about X, and where?"). It must answer only from my material and say so when the material does not contain the answer.

Nine originals are kept unchanged in `vault/raw/` (SHA-256 in the [Source Catalog](vault/Source%20Catalog.md)):

| Original | What it is |
|---|---|
| `Economics Lectures.md`, `Data and Decisions Lectures.md` | my own-words summaries of the 9 + 10 lecture slide decks (slides **not** published; summaries written with Claude's help, one `## Lecture N` section each) |
| `Sunk Cost Reasoning`, `Relevant Cost`, `Supply and Demand Shocks`, `Group Pricing`, `Menu Pricing`, `Durable Advantage` (`.docx`) | my own "Examples in the Wild" assignments |
| `AuraTech Case.docx` | my own Data & Decisions case write-up (regression interpretation) |

**How originals connect to wiki pages.** `wiki-plan.toml` lists the 27 pages (title, topic folder, search words) and the sources. For each page the
harness retrieves the relevant passages from all originals, Gemma writes the note, and the harness records exactly which passages the note cites
(`source_passages` and `source_files` in its properties, plus a `## Sources` section and links to `raw/`). Notes are grouped in three topic folders
(`Economics/`, `Data Analysis/`, `Cases/`); file names are the page titles (2-6 words), the first heading matches the file name, and machine data
(fingerprints, chunk ids, hashes) lives in the note's properties, never in its name.

Honest scope notes: the lecture summaries are derived from slides I do not have the right to publish, so only my own-words summaries are in the repo;
my graded assignments are included, so check your course's honor code before reusing this approach. A sixth Word document (the Uber case) was
**left out** because it contained a local file path with my Windows user name.

## Setup and device
| Item | Value |
|---|---|
| OS | Windows 11 Home 10.0.26200 (ARM64) |
| CPU | Snapdragon X Plus, 8 cores @ 3.3 GHz |
| RAM | 15.6 GB total. Typically only **0.8-1.7 GB free** while Slack, ChatGPT, Claude etc. are open |
| GPU | Qualcomm Adreno X1-45 (integrated, no dedicated VRAM); the model runs **100% on CPU** (`ollama ps`) |
| Disk | about 293 GB free |
| Runtime | Ollama 0.34.3 (native ARM64), Python 3.12.10 (ARM64) |
| Model | `gemma4:e2b`, 5.1B parameters (including embedding tables), **Q4_K_M**, 7.2 GB file, digest `7fbdbf8f5e45a75b...a47e` (full digest in every evidence card) |
| Retrieval | SQLite FTS5 (BM25 ranking, Porter stemming), standard library only; **no embeddings, no hosted service** |

**Why this model.** It is the smallest Gemma size on offer. 26B would not load in 15.6 GB, and E4B would leave too little memory next to other applications.
Measured: about 6.9 GB in total at an 8,192-token context (`llama-server` process: 2.9-3.2 GB working set, up to 5.6 GB private), roughly 23 tokens/s
generation on the CPU. Its weakness is exactly what the tests found: a 5B model tends to answer with the closest related fact instead of refusing.
(Google's memory table quotes about 2.9 GB for E2B at Q4_0; the Ollama file is larger because it is Q4_K_M and includes embedding tables.)

**Model source and exact identifier.** Model weights are **not** in this repository. Official sources: the model page in the Ollama library, <https://ollama.com/library/gemma4> (tag `gemma4:e2b`), and Google's Gemma documentation, <https://ai.google.dev/gemma/docs>. Identifier used for every result here: `gemma4:e2b`, quantization Q4_K_M, Ollama digest `7fbdbf8f5e45a75bb122155ed546e765b4d9c53a1285f62fd9f506baa1c5a47e` (short id `7fbdbf8f5e45`), runtime Ollama 0.34.3. Gemma is distributed under its own license terms from Google, which apply when you download it.

**Install (needs internet once, to download).**
```powershell
git clone https://github.com/PLPSA25/personal-wiki-gemma.git ; cd personal-wiki-gemma
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"      # installs the `wiki` command, PyYAML and pytest
ollama pull gemma4:e2b                                   # about 7 GB; stored in %USERPROFILE%\.ollama, never in the repo
ollama serve                                             # local server on 127.0.0.1:11434 (leave running)
```
No embedding model and no other download is needed. After this, nothing requires the internet.

**Run.**
```powershell
.venv\Scripts\wiki.exe --help
.venv\Scripts\wiki.exe ingest ./vault/raw                # ~33 min the first time; later runs skip notes that are up to date
.venv\Scripts\wiki.exe search "group pricing" --limit 3  # no model
.venv\Scripts\wiki.exe ask "What sample size guarantees a margin of error of plus or minus 3 percentage points in a political poll?" --mode local
.venv\Scripts\wiki.exe chat                              # /help, /notes <message>, /search <words>, /clear, /exit
.venv\Scripts\wiki.exe chat --script demo\chat-script.txt   # reproducible scripted session
.venv\Scripts\wiki.exe approve --all                     # after reviewing the notes in Obsidian
.venv\Scripts\python.exe evals\run_evals.py --label my-run          # the four ask tests, saves evidence cards
.venv\Scripts\python.exe evals\run_mode_checks.py --label my-run    # chat / search / boundary checks
.venv\Scripts\python.exe -m pytest                                  # 321 unit tests, no Ollama needed (~16 s)
```
Errors are one plain line and a non-zero exit code, never a stack trace (model server stopped, model missing, no index, missing file,
non-local model address). `wiki ask` prints "(`wiki search` works without the model...)" when the model is unavailable.

### Measured time and memory
| Action | Time | Notes |
|---|---|---|
| `wiki ingest`, 27 notes | **1,995 s (33 min)**, 74 s per note on average | [evidence](evidence/ingest/README.md); model process 2.85 GB working set on average (peak 3.18 GB), up to 5.6 GB private |
| `wiki ask`, a new question, model already loaded | **105 s** (answer 81 s + verification 24 s) | measured with the laptop's other apps open (0.9 GB free RAM); a lot of the time is Gemma *reading* about 1,800 prompt tokens on the CPU |
| `wiki ask`, cold start (model unloaded) | **120 s** (answer 84 s incl. 8 s model load + verification 35 s) | |
| `wiki ask`, same question again | 1-5 s for the model | Ollama reuses the cached prompt, so the times inside the evidence cards are **not** representative |
| `wiki ask`, offline demo, other apps closed (2.8 GB free RAM) | **33-65 s** per question (answer 23-46 s + checks 9-22 s); the four tests took 3 min 52 s | [transcript](evidence/offline-demo/stage2-20260927-225204.txt); memory afterwards: `llama-server` 3.16 GB working set, 3.75 GB private, 3.1 GB RAM free |
| `wiki search` | 0.35 s | no model |
| `wiki chat` reply | about 1-25 s | longer when notes are attached |

## Architecture
* **Model** - Gemma, running in Ollama. It only turns the text it is sent into more text. It does not read files, remember anything, or run tools.
* **Retrieval tool** - `retrieval.py` over the SQLite index (`index.py`): returns original passages with source, section and line range.
* **RAG workflow** (ask) - retrieve, put the passages in the prompt with instructions, call the model, check the result.
* **CLI** - `cli.py`: parses the command, prints results and errors. It contains no logic beyond dispatch.
* **Harness** - everything in between: modes and their different instructions and context, when to retrieve, prompt assembly, model calls,
  citation and answerability checks, error handling, and saved outputs (`data/logs`, `evidence/`).

```
wiki ask "Q" -> cli.py --> ask.answer_question
                 1 retrieval.search(index.db)          top 5 passages, labelled S1..S5, source+lines
                 2 prompts.build_ask_messages          wiki-instructions.md + passages (as data) + question. No persona, no history
                 3 llm.OllamaClient.chat               local only (loopback check), think off, temperature 0.1, seed 7
                 4 ask.interpret_reply                 INSUFFICIENT_EVIDENCE? the harness shows its own fixed sentence
                 5 citations.check_answer              cited labels must exist; every number/month must appear in the cited passage
                 6 verify.check_answerable (fact questions only, never sees the draft) + verify.verify_answer (sees draft + cited passages)
                 7 answer + cited passages + model identity + timing shown, run appended to data/logs/ask.jsonl
                 a draft failing 5 or 6 is WITHHELD and shown as "insufficient evidence" (the draft is kept in the log)
wiki search  -> retrieval.search only; no model is constructed.
wiki chat    -> chat.ChatSession.say: router.decide_route -> (search + attach passages | attach capability list | nothing)
                 -> persona.md + generated capability list + last 8 messages + message -> model (streamed) -> citation check if notes were attached
wiki ingest  -> plan.load_plan -> index.build_index -> per note: gather passages -> ingest.link_candidates -> model (JSON schema)
                 -> validate_note (citations, figures, links, required sources; one retry with the reason) -> vault.render_note -> index.md + Source Catalog
```

**Context management.** Ask sends at most 5 passages of up to 1,200 characters (about 1,500-1,800 tokens including instructions); ingest 6-8 passages
(about 2,000-2,500 tokens); chat sends the persona and capability list, the last 8 messages (capped at 5,000 characters, oldest exchange dropped first)
and, only when needed, 4 passages. History stores plain conversation only; passages are re-fetched when needed and never remembered as evidence.
The whole wiki is never sent.

## Design choices
* **Passage size: up to 1,200 characters**, split at headings then paragraphs, then sentences (`chunk.py`). Each passage keeps source, section and line range (for
  `.docx` the lines refer to the extracted text). Small enough to cite precisely and to fit five in the prompt; a passage cut mid-paragraph can start mid-thought,
  which is a known cost. Overlap between passages would be the fix.
* **Retrieval: keyword BM25** over the passages, section titles weighted double, common words removed, all user text quoted so it cannot act as search syntax.
  Chosen because it is dependency-free, runs offline in 0.35 s, and its misses are easy to inspect. Its weakness: it matches words, not meaning (test 2's key passage ranks 4th).
* **Research rules and personality are separate files.** Ask loads only `wiki-instructions.md`; chat loads `persona.md` plus a capability list generated from the real vault, so
  it cannot promise commands that do not exist.
* **When chat retrieves** (`router.py`, rules in order): greetings, questions about the assistant, follow-ups on the previous reply, and drafting/brainstorming requests never
  search; mentioning "my notes" always does; a content question searches and needs a weak minimum match. Search score alone cannot decide (a study-plan request scores
  8.5, "explain marginal revenue" 5.5). The route is printed under every reply. `/notes <message>` forces a lookup.
* **Naming and folders:** titles come from `wiki-plan.toml`, validated (2-6 words, no path characters, unique), so Gemma can never choose a file name or write outside `vault/wiki/`.
* **Re-ingestion without duplicates:** a note's file name is its title, so it is always overwritten in place. A fingerprint of everything that shapes a note (passages, plan
  entry, instructions, model, link candidates, format version) decides whether to regenerate; reviewed or hand-edited notes are protected and old versions backed up.
  Proven by `wiki ingest` twice: `27 up to date`, 0 s, no model call.
* **Model settings that mattered:** thinking off (`think: false`; faster and no hidden text in answers); temperature 0.1 and a fixed seed for ask; a context window of 8,192;
  JSON-schema output for ingest so a note is always parseable; low answer-token caps (400 for ask, 700 for chat).
* **Security:** passages are delimited data and cannot close their own block; the model has no tools and nothing it writes is executed; all model text is stripped of HTML,
  `[[links]]` and control characters before reaching a file; `.docx` reading refuses zip bombs and XML entity declarations; the SQLite index is opened read-only for queries with
  parameterized SQL; the Ollama URL must be this computer (no proxies, no redirects, no cloud fallback); `raw/` is only ever read; `.gitignore` excludes weights and secrets.

## Evidence
### The four ask-mode tests (final-index run and the offline run [`offline-20260927-225204`](evidence/ask-tests/offline-20260927-225204/summary.md), both 4/4; details and history in [evidence/ask-tests/README.md](evidence/ask-tests/README.md))
Questions and expected evidence were written before any retrieval code existed ([questions.toml](evals/questions.toml)); retrieval was inspected first
([retrieval-check.md](evidence/retrieval-check.md)).

| # | Question | Retrieved (expected passage) | Answer (final run) | Verdict |
|---|---|---|---|---|
| 1 | What sample size guarantees a margin of error of plus or minus 3 percentage points in a political poll? | rank 1, Data Lecture 5 | "1,112 people ... [S1]" | correct, cited passage says 1/(0.03 squared) = 1,112 |
| 2 | Why can't a monopolist just keep producing until price equals marginal cost? (reworded) | rank **4**, Economics Lecture 5 (ranks 1, 2 and 5 are the price-taker lecture) | extra unit cuts the price on all units, so marginal revenue < price [S4] | correct and supported, but starts with a garbled word ("monopolist't") |
| 3 | What three conditions must hold for group pricing, and how does the Netflix example satisfy them? (two sources) | ranks 1-3, Lecture 6 + `Group Pricing.docx` | all three conditions, each mapped to the Netflix example [S1-S3] | correct, one citation *warning* (uncited lead-in) |
| 4 | When is the MBA 201A final exam? (**unsupported**) | passages about the exam's *weight*, no date | "Insufficient evidence: the wiki does not contain the information needed to answer this question." | correct |

**The unsupported question failed at first, and the fix took three attempts** (cards for every run are kept):
run 1 answered "40% of the grade" (a weight, from the wrong course); instruction rewrites moved the failure around (run 2 broke tests 1 and 2, run 3 failed test 4 again
*with the citation check saying OK* because the quoted 40% really was in the cited passage); the fix that held is in the harness, not the prompt: a draft-free "answerability"
check for fact-seeking questions plus a draft verification. [`replay-run3-draft`](evidence/ask-tests/replay-run3-draft/test-4.md) replays run 3's exact bad draft through the real checks:
the citation check passes it, the answerability check says `KIND: date | VERDICT: NO`, and it is withheld. The final runs caught test 4 via the simpler figure check; the replay proves the deeper layer.
A citation is not proof: each card has an assessment written after reading the cited passages. **These assessments are drafts by Claude; the student's own confirmation against the sources is still required.**

### Chat and search mode checks ([evidence/mode-checks](evidence/mode-checks/README.md))
Six automated checks, all passing in the final runs (online and, offline, [`offline-20260927-225650`](evidence/mode-checks/offline-20260927-225650/transcript.md)); earlier failed runs are kept: "what can you help me with?" / "what can we do?" explain the real commands and suggest a starting
point with no notes search, no citations and no refusal; a drafted plan followed by "make that shorter" uses the conversation; a notes question searches and cites;
`search` prints original passages with no model call; and a claim made only in chat ("my exam is on December 5th") is **not** evidence in ask mode.

### Offline demonstration
`demo/offline-demo.ps1 -Stage 1|2|3` runs the demonstration in three short stages with the internet disconnected. Every stage first proves the machine is offline (TCP to 1.1.1.1, DNS and HTTPS to example.com must all fail; each transcript shows `OFFLINE CONFIRMED`), restarts Ollama and the CLI, and saves a redacted transcript with the command output.

| Stage | What it shows | Transcript | Result |
|---|---|---|---|
| 1 | `wiki --help`; `wiki ingest` of a source in a scratch project, then again (nothing rewritten); `wiki search` | [stage1](evidence/offline-demo/stage1-20260927-222845.txt) | ingest 31.6 s, note written, second ingest `up to date` |
| 2 | the four ask-mode tests | [stage2](evidence/offline-demo/stage2-20260927-225204.txt), cards in [`ask-tests/offline-20260927-225204`](evidence/ask-tests/offline-20260927-225204/summary.md) | 4/4 pass in 3 min 52 s |
| 3 | chat capability questions, follow-up, notes turn, search-only, and the chat-claim-is-not-evidence boundary; a scripted chat; memory | [stage3](evidence/offline-demo/stage3-20260927-225650.txt), [`mode-checks/offline-20260927-225650`](evidence/mode-checks/offline-20260927-225650/transcript.md) | 6/6 pass |

A 29-second screen recording of the PowerShell window made during the offline run is in [`evidence/recording/`](evidence/recording/README.md) (condensed by the student; the full output is in the transcripts above).

The demonstration took four attempts (a script bug, an unexplained laptop shutdown, then a 5/6 mode-check result that exposed a wrong claim by the assistant); all are recorded in [evidence/offline-demo/README.md](evidence/offline-demo/README.md) and [evidence/mode-checks/README.md](evidence/mode-checks/README.md).

### Obsidian screenshots
Open `vault/` itself as the vault. Filter used for the graph: `path:wiki/` with **Attachments** turned off.
* Open note with source references and related links: `evidence/screenshots/note.png`
* Page list / index: `evidence/screenshots/index.png`
* Graph view: `evidence/screenshots/graph.png`
* Source catalog: `evidence/screenshots/source-catalog.png` ([`vault/Source Catalog.md`](vault/Source%20Catalog.md): each original, what it is, its SHA-256 and the notes that cite it).
* Trace from a note to a related note and back to the original evidence: `evidence/screenshots/trace.png`. The path: open `Group Pricing` -> its related note `Two-Part Tariffs` ("Two-part tariffs price at marginal cost and take the surplus as a fee, limited by arbitrage and uncertainty") -> its `## Sources` link `Economics Lectures - Lecture 5 (lines 215-224)` -> the original passage in `vault/raw/Economics Lectures.md`, whose SHA-256 is in the catalog.

## Reflection: one real limitation and one improvement
**Limitation.** Correctness against a *near miss* is the hard case for a 5B model. Asked for a date, it will offer a grade weight; asked for "the MBA 201A" weight, it can take the
number from the Data & Decisions course. In my experiment the draft-free answerability check said YES to that wrong-course case (it cannot tell courses apart), and the draft-aware verifier said NO in the one trial I ran, which is too little to rely on. The
figure check and the answerability check catch most such answers, but a confident mistake of the "right kind of fact, wrong course" type can still get through. Speed is the second
limit: a fresh question takes 33-65 s with other apps closed and about two minutes when the laptop is crowded, because the answer and each check re-read about 1,800 tokens on a CPU.
**Improvement I would try.** Tag every source with its course in `wiki-plan.toml` and filter retrieval by any course the question names (for example "MBA 201A"), so a passage from the other
course is never in the prompt; then shorten the prompt (top 4 passages, 800-character passages, overlap between passages). Expected effect: removes the wrong-course confusion and cuts the
read time roughly in half. Embeddings could improve retrieval of reworded questions (test 2) but need a second local model in memory that this laptop does not have.

## Known limitations (also honest notes)
* The lecture summaries are the evidence and were written by an AI from the slides. Every number in them was matched automatically against the slide text, and the student spot-checked 8 items across 8 of the 19 lectures against the slides, all matching ([evidence/review/lecture-summary-spot-check.md](evidence/review/lecture-summary-spot-check.md)). That is a spot-check, not a full audit. Wiki notes stay `status: draft` (see the review status below).
* **Review status (honest):** a review of all 27 notes was performed by Claude at the student's request ([evidence/review/wiki-review.md](evidence/review/wiki-review.md)): structure and links were checked automatically, and all 153 key points were compared with the passages their links cite. It found **5 key points (3%) with a wrong source reference** (one cited the wrong document, four the wrong lecture section; the claims themselves were supported) and they were corrected in the wiki; the student found the first one in Obsidian. The student has not independently reviewed every note, so all notes remain `status: draft`. Ingest does not catch this kind of slip because it checks that a cited passage exists and that numbers match, not that a point's words are in the passage its link names.
* "Related notes" reasons are model-written and only checked for existence; a few are weak. Two are left in the wiki unfixed on purpose and documented in [evidence/review](evidence/review/wiki-review.md): `Hypothesis Testing` -> `Decision Trees` (the reason itself says "no clear connection") and `Cost Disease` -> `Omitted Variable Bias` (a stretch).
* Scout does not always label its drafts "Suggestion:" although its rules say so.
* The chat router and the "fact-seeking question" detector are hand-written rules calibrated on a small set of messages.
* Online mode is not implemented; local mode is the only mode.

## Repository layout
```
src/wiki/     the CLI and harness          prompts/   all instruction files        vault/     raw/ (originals), wiki/ (notes), index.md, Source Catalog.md
tests/        321 pytest tests             evals/     answer key, runners, plan    evidence/  results, cards, transcripts, screenshots
demo/         offline demo script          wiki-plan.toml   the 27 pages and their sources     data/  (git-ignored) index, logs, backups
```
