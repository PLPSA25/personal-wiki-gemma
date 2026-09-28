# Ask-mode tests: what was tried, what failed, what changed

Four fixed questions (`evals/questions.toml`, written before any retrieval code existed) were run in **ask mode, local**
(Gemma `gemma4:e2b` through Ollama, no internet needed for the run) after every change. Each run has its own folder with
one evidence card per test (question, expected evidence, retrieved passages with paths, model identity, answer, checks,
assessment), a `summary.md`, `results.json` and the exact instruction files it used. Earlier runs are kept as evidence
of what improved and what stayed wrong.

| Run | What changed | Test 1 | Test 2 | Test 3 | Test 4 (unsupported) |
|---|---|---|---|---|---|
| [run-1-initial](run-1-initial/summary.md) | first version of `wiki-instructions.md` | pass | pass (garbled first word) | pass (one point omitted) | **FAIL**: answered "40% of the grade" instead of refusing |
| [run-2-instructions-v2](run-2-instructions-v2/summary.md) | added a step-by-step routine and a refusal example | pass, but the model **printed the steps** | **FAIL**: refused a question it could answer | pass | pass, but its refusal sentence contained a wrong claim (40%) |
| [run-3-instructions-v3](run-3-instructions-v3/summary.md) | "think silently", "different words count", refuse with one word; harness drops any text the model adds to a refusal | pass | pass | pass | **FAIL** again, and the citation check said OK (the model cited the Data and Decisions passage, which really contains 40%) |
| [run-4-with-verification](run-4-with-verification/summary.md) | harness adds a yes/no verification of the draft against the cited passages | pass | pass | pass | pass (caught by the figure check, not by the verifier) |
| [run-5-answerability-check](run-5-answerability-check/summary.md) | harness adds a draft-free answerability check for fact-seeking questions | pass | pass | pass | pass (again caught by the figure check) |
| [run-6-final-index](run-6-final-index/summary.md) | none (rerun after the Uber case was removed: 9 sources, 114 passages) | pass | pass | pass | pass |
| [replay-run3-draft](replay-run3-draft/test-4.md) | replays run 3's bad draft through the real checks | | | | **withheld by the answerability check** (`KIND: date | VERDICT: NO`) |

## What the experiments taught
1. **Instructions alone were not reliable for a 5B model.** Version 2 fixed test 4 and broke tests 1 and 2; version 3 did the
   opposite. Prompt wording moved the failure around instead of removing it.
2. **A citation is not proof.** Run 3's citation check said OK to a wrong answer, because the number it quoted really was in the
   cited passage; it just belonged to a different course and was the wrong kind of fact.
3. **The verifier was anchored by the draft.** Shown the draft answer, it said YES to run 3's failure (the draft's "40%"
   matched the passage). Shown only the question and passages, it said NO. But the draft-free check wrongly refused open-ended
   questions (tests 2 and 3), so it runs only for fact-seeking questions (when / where / who / how many / what date...).
   Experiment (8 labelled cases, two variants): draft-free variants B and C were 5/8, each wrong on tests 2, 3 and one wrong-course case.
4. **Known remaining weakness:** a question naming one course (e.g. "the MBA 201A weight") can still be answered from the other
   course's passage; both verifiers said YES to that case. Proposed improvement: tag each source with its course and filter
   retrieval by the course named in the question.
5. **The router for fact-seeking questions is a heuristic** (a regular expression on the first words of the question). It was
   designed after seeing failures and would need a better classifier for other question styles.

## Timing note
Ollama caches the prompt of an identical previous request, so answer times inside these cards (1-5 s in runs 4-5) are far
lower than a cold first request (about 25-45 s here, mostly reading a 1,200-1,700 token prompt on the CPU). Response times in the
README are measured from cold runs only.
