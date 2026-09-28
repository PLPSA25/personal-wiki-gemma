# Baseline measurements (Milestone 0)

Raw numbers recorded before any harness code existed. Mode: **local** (Ollama on 127.0.0.1). No chat/ask/search involved.

## Device
| Item | Value |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| CPU | Snapdragon X Plus (8-core, ARM64) @ 3.30 GHz |
| GPU | Qualcomm Adreno X1-45 (integrated, no dedicated VRAM) |
| Total RAM | 15.6 GB |
| Free disk (C:) | ~293 GB |
| Python | 3.12.10 (ARM64) |
| Ollama | 0.34.3 |

## Model (from `ollama show gemma4:e2b`)
- architecture `gemma4`, 5.1B parameters (includes embedding tables), quantization **Q4_K_M**, on-disk blob 7.16 GB
- Ollama defaults: temperature 1, top_k 64, top_p 0.95; thinking enabled by default; supports a 131072-token context

## First response (one sentence RAG definition, `think=false`, `num_ctx=4096`)
| Metric | Value |
|---|---|
| Wall time | 8.1 s |
| Model load | 5.7 s |
| Prompt tokens / generated tokens | 20 / 39 |
| Generation speed | 22.7 tokens/s |
| Runs on | 100% CPU (`ollama ps`) |
| Model memory while loaded | 6.7 GB (`ollama ps`, context 4096) |

## Caveats (honest notes)
- Free RAM was already only 1.7 GB of 15.6 GB before loading the model (other apps open) and 0.4 GB afterwards.
  "Free" excludes cached memory, so this is not necessarily a problem, but it means the machine is under memory pressure.
- Windows Task Manager per-process figures for the Ollama runner have not been captured yet; the final README will use
  a repeatable measurement taken during ingestion and an ask query.
- This is a single, cold-start measurement; more runs will be recorded in Milestone 6.
