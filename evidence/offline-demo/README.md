# Offline demonstration

Run with `demo/offline-demo.ps1`, in three stages (`-Stage 1`, `-Stage 2`, `-Stage 3`), Wi-Fi and Ethernet switched off. Each stage first proves the machine is offline (TCP, DNS and HTTPS to
the internet must all fail), restarts the local model server and the CLI, and saves its own redacted transcript here.

## Failed attempts (kept as an honest record; their output was discarded because it cannot prove an offline run)
1. **Attempt 1, script bug:** the script wrote a temporary plan file with a byte-order mark, which the TOML parser rejected at the "ingest a source" step. Fixed in the script, and the tool
   now also tolerates a byte-order mark (`test_a_plan_saved_with_a_windows_byte_order_mark_still_loads`).
2. **Attempt 2, the laptop shut down unexpectedly** (Windows Kernel-Power event 41, bug-check code 0: a hard hang or power/thermal cut-off, not a software crash; cause not identified),
   as the run reached the mode checks, about 25 minutes into the demo. The kept transcript ([attempt2-interrupted-transcript-redacted.txt](attempt2-interrupted-transcript-redacted.txt))
   shows `OFFLINE CONFIRMED` and the offline ingestion of a source, then stops. The four ask-mode test cards of that run had been written, but the assistant **deleted them by mistake**
   (it believed the transcript had been lost); stage 2 regenerates them. The demo was then split into three short stages and the mode-check runner now saves after every check.
3. **Attempt 3 (stages 1-3, all offline, no errors)** - transcripts `stage1-*.txt`, `stage2-*.txt`, `stage3-*.txt` each show `OFFLINE CONFIRMED`. Two problems found in the review of these transcripts:
   the stage 2 and 3 transcripts recorded only the PowerShell headers, not the output of the commands that produce their results (native program output is not captured by `Start-Transcript` unless it is
   piped through `Out-Host`); and the mode checks scored 5/6 (see [mode-checks](../mode-checks/README.md)). The script now pipes command output through `Out-Host`, the chat defect was fixed, and stages 2 and 3
   were run again (attempt 4). The results of attempt 3 (`ask-tests/offline-20260927-223004`: 4/4 pass; `mode-checks/offline-20260927-223518`: 5/6) are kept.
4. **Attempt 4 (stages 2 and 3 again, offline, no errors)** after the fixes: stage 2 4/4, stage 3 6/6, transcripts now contain the command output. These are the runs cited in the README.
