# Chat / search / ask boundary checks: what was tried and what changed

Produced by `python evals/run_mode_checks.py --label <run>` (real local Gemma, mode: chat/search/ask, execution: local).
Each folder holds `transcript.md` (every message, reply, routing decision, citation check and automated verdict) and `results.json`.

| Run | What changed | Result |
|---|---|---|
| [mode-checks-1](mode-checks-1/transcript.md) | first persona and chat harness | 4/6. **A failed twice**: Scout avoided a notes search and any refusal (good) but its capability answer named none of the real commands and gave no starting point. **B "passed" wrongly**: asked for a plan, Scout asked a clarifying question instead of drafting, and "make that shorter" produced another question; my check only compared lengths. |
| [mode-checks-2-persona-v2](mode-checks-2-persona-v2/transcript.md) | persona: "draft first, ask afterwards"; "answer capability questions from the real list"; stricter checks | 4/6. "what can you help me with?" passed. "what can we do?" still vague (a 5B model does not reliably use a list buried in a long system prompt). B now correctly produced a draft, but my new "must not end with a question" check was over-strict. |
| [mode-checks-3-capabilities-attached](mode-checks-3-capabilities-attached/transcript.md) | harness change: for questions about the assistant itself, the program attaches the real capability list to that turn (as it attaches passages for notes questions); B now checks for an actual list instead of banning questions | **6/6** |

## Honest notes on the final run
- The routing works as designed, but it is rule-based (see `src/wiki/router.py`). It was calibrated on a handful of messages; unusual phrasings can
  be misrouted. `/notes <message>` forces a lookup and `/search <words>` shows raw passages.
- Scout's draft was not introduced as a "Suggestion:" although `prompts/persona.md` asks for it. The model follows that rule only sometimes.
- Check E (chat claim is not evidence in ask): the December date said in chat never reaches ask mode, because ask builds its prompt only from
  `wiki-instructions.md`, the retrieved passages and the question (see the unit test `test_what_is_said_in_chat_is_never_evidence_for_ask`).
- Check D (search): passages and source locations are printed with no model call (the check counts model calls: 0).

## Offline run 1 (stage 3 of the offline demo): 5 of 6, and what it revealed
[`offline-20260927-223518`](offline-20260927-223518/transcript.md), run with the internet disconnected: **"what can we do?" failed** (it did not name the commands). Reading both capability replies
also showed a defect that the check had not been testing: Scout said it "can run terminal commands like `wiki ask`". It cannot; the student types them. At temperature 0.6 the answer also varied from run to run.

Fixes: the generated capability text now says the *student* types the commands and the assistant cannot run them; the persona says the same; capability turns use a low temperature (0.2); and the check now
fails a reply that claims the assistant can run commands. Stability after the fix, over 5 fresh sessions x 2 questions with real Gemma ([capability-stability.json](capability-stability.json)):
**10/10 replies name `wiki ask` and `wiki search`, 0/10 claim they can run commands, 10/10 suggest a starting point.** The earlier offline result is kept as it was; the demo's stage 3 is re-run after the fix.
