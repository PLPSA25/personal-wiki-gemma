# Ingestion evidence

Command: `wiki ingest` (mode: local; model `gemma4:e2b` Q4_K_M through Ollama 0.34.3; CPU only). It rebuilds the search index
(114 passages from 9 sources), then has Gemma write each of the 27 notes listed in `wiki-plan.toml` from the passages found for it,
validates every note (citations, figures, links) and regenerates `vault/index.md` and `vault/Source Catalog.md`.

| Run | What it shows | Result |
|---|---|---|
| [ingest-run-1-unrefined-links.txt](ingest-run-1-unrefined-links.txt) | the first complete run: gave Gemma the whole plan as possible link targets | 27 written in 1,840 s. Every link resolved, but many "related note" links were weak (Group Pricing linked to Sunk Costs and Cost Disease, not to Menu Pricing; one page had no links). |
| [ingest-run-2-final.txt](ingest-run-2-final.txt) | the final run: code offers only notes whose evidence overlaps the page's | 27 written in 1,995 s (33 min); pages have 1-4 links, none broken |

Lines starting with `dropped from` show the harness discarding what it could not verify: related links to pages that are not in the plan
(for example `'Monopolistic competition'`, `'Sunk costs'`) and a key point without a valid citation.

## Measurements (final run, 2026-09-27, 19:55-20:28)
| Measure | Value |
|---|---|
| Wall time, 27 notes | 1,995 s (33.3 min); per note: average 74 s, fastest 62 s, slowest 100 s |
| Model process (`llama-server`) memory | working set average 2.85 GB, peak 3.18 GB; private memory peak 5.57 GB; `ollama ps` reports 6.9 GB in total at an 8,192-token context (the weights are memory-mapped) |
| Free RAM on the whole laptop | as low as 0.84 GB of 15.6 GB (Slack, ChatGPT, Claude and other apps were open, which slowed the run) |
| Output | 27 notes, about 10,600 words; search index 232 KB |

Raw samples every 15 s: [memory-samples-llama-server.csv](memory-samples-llama-server.csv) (columns: time, working set GB, private GB, available RAM GB;
the file also covers run 1 and the idle time between runs, where the model process was unloaded and shows 0).

## Text passed to Gemma per note
Up to 6 passages (7-8 for the case pages), each at most 1,200 characters, plus the instruction file (about 1,600 characters) and the list of
link candidates: roughly 8,000-9,000 characters or 2,000-2,500 tokens per call. Notes are never generated from a whole source at once.

## Re-ingestion
A second `wiki ingest` with unchanged sources writes nothing and does not call the model (every note reports `up to date`; unit test
`test_re_ingest_changes_nothing_and_does_not_call_the_model`). A changed source regenerates only the notes that use it and backs up the old
version to `data/backup/`; a note marked `reviewed` (`wiki approve`) or edited by hand is never overwritten unless `--force` is given.
