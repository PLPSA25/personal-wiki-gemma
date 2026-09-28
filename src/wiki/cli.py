"""Command-line interface: a thin layer that parses the command and calls the harness.

Every command returns an exit code (0 = ok, 1 = a problem the user can fix, 2 = bad usage) and
expected problems are printed as one clear line, never as a stack trace.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .ask import answer_question, format_result, save_run
from .chat import ChatSession
from .config import Paths, default_root
from .errors import ModelError, WikiError
from .index import build_index
from .ingest import approve, ingest
from .llm import DEFAULT_MODEL, DEFAULT_OLLAMA_URL, LanguageModel, OllamaClient
from .plan import load_plan
from .prompts import passage_label
from .retrieval import DEFAULT_LIMIT, search

_DESCRIPTION = """\
Personal wiki: talk to your own notes with a local model, fully offline.

Commands:
  chat     talk with the study assistant: brainstorm, draft, follow up (uses the local model)
  ingest   read vault/raw and write the linked wiki notes, index.md and Source Catalog (uses the local model)
  approve  mark notes you have reviewed, so re-ingesting never overwrites them
  ask      a neutral, cited answer from your notes, or "insufficient evidence" (uses the local model)
  search   show the original passages that match your words (no model involved)
  index    (re)build only the local search index from the files in vault/raw
"""

_EXAMPLES = """\
examples:
  wiki chat
  wiki ingest ./vault/raw
  wiki approve --all
  wiki index
  wiki search "margin of error poll"
  wiki search "group pricing" --limit 3
  wiki ask "What is the golden rule for a price-taking firm?" --mode local

Local mode is the only mode: the model runs on this computer through Ollama (start it with
"ollama serve"; download the model once with "ollama pull gemma4:e2b"). Nothing leaves the machine.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki",
        description=_DESCRIPTION,
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"wiki {__version__}")
    parser.add_argument(
        "--root", type=Path, default=None,
        help="project folder containing vault/ and data/ (default: $WIKI_ROOT or the folder of this program)",
    )
    commands = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    search_cmd = commands.add_parser(
        "search", help="show original matching passages (no model)",
        description="Show the original passages that best match your words, with their source file and "
                    "section. Uses only the local keyword index: no language model, works with Ollama stopped.",
    )
    search_cmd.add_argument("query", help="the words to look for, e.g. \"marginal revenue monopoly\"")
    search_cmd.add_argument("--limit", type=int, default=DEFAULT_LIMIT, metavar="N",
                            help=f"maximum passages to show (default: {DEFAULT_LIMIT})")
    search_cmd.set_defaults(handler=_cmd_search)

    ask_cmd = commands.add_parser(
        "ask", help="cited, evidence-only answer (uses the local model)",
        description="Answer one factual question using only passages retrieved from your notes. Each question is "
                    "independent: no chat history and no assistant personality are used. The answer must cite the "
                    "passages it uses, or say that the evidence is insufficient.",
    )
    ask_cmd.add_argument("question", help="the question to answer from your notes")
    ask_cmd.add_argument("--mode", choices=["local"], default="local",
                         help="where the model runs; only 'local' (this computer) is available")
    ask_cmd.add_argument("--top-k", type=int, default=DEFAULT_LIMIT, metavar="N",
                         help=f"passages given to the model (default: {DEFAULT_LIMIT})")
    ask_cmd.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    ask_cmd.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL,
                         help=f"local Ollama address (default: {DEFAULT_OLLAMA_URL}); must be this computer")
    ask_cmd.add_argument("--no-log", action="store_true", help="do not save this run to data/logs/ask.jsonl")
    ask_cmd.set_defaults(handler=_cmd_ask)

    ingest_cmd = commands.add_parser(
        "ingest", help="write the wiki notes from vault/raw (uses the local model)",
        description="Rebuild the search index, then have the local model write every note listed in wiki-plan.toml "
                    "from the passages it finds in vault/raw, and regenerate index.md and the Source Catalog. "
                    "Notes whose inputs did not change are skipped; notes you reviewed or edited are never "
                    "overwritten unless you pass --force (the old version is backed up first).",
    )
    ingest_cmd.add_argument("raw", nargs="?", type=Path, default=None,
                            help="folder with the original sources (default: vault/raw of the project)")
    ingest_cmd.add_argument("--only", action="append", metavar="TITLE", help="only (re)write this note; repeatable")
    ingest_cmd.add_argument("--force", action="store_true", help="regenerate even reviewed or edited notes (backed up)")
    ingest_cmd.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    ingest_cmd.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL,
                            help=f"local Ollama address (default: {DEFAULT_OLLAMA_URL}); must be this computer")
    ingest_cmd.set_defaults(handler=_cmd_ingest)

    approve_cmd = commands.add_parser(
        "approve", help="mark notes as reviewed",
        description="Mark notes as reviewed after you checked them against their sources in Obsidian. "
                    "A reviewed note is protected from being overwritten by a later ingest.",
    )
    approve_cmd.add_argument("titles", nargs="*", metavar="TITLE", help="note titles to approve")
    approve_cmd.add_argument("--all", action="store_true", help="approve every note")
    approve_cmd.set_defaults(handler=_cmd_approve)

    chat_cmd = commands.add_parser(
        "chat", help="talk with the study assistant (uses the local model)",
        description="Chat with Scout, a study assistant: brainstorm, draft, plan, and follow up on earlier replies. "
                    "The notes are searched only when your message needs them, and then the reply cites them. "
                    "In chat: /help, /notes <message> (force a notes lookup), /search <words> (raw passages, no model), "
                    "/clear (forget the conversation), /exit.",
    )
    chat_cmd.add_argument("--script", type=Path, metavar="FILE",
                          help="read the messages from a text file (one per line) instead of the keyboard; "
                               "used for reproducible demos and the mode checks")
    chat_cmd.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    chat_cmd.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL,
                          help=f"local Ollama address (default: {DEFAULT_OLLAMA_URL}); must be this computer")
    chat_cmd.set_defaults(handler=_cmd_chat)

    index_cmd = commands.add_parser(
        "index", help="rebuild the search index from vault/raw",
        description="Read every source in vault/raw (.md, .txt, .docx), split it into passages and rebuild the "
                    "local keyword index. Sources are only read, never changed.",
    )
    index_cmd.set_defaults(handler=_cmd_index)
    return parser


def _cmd_index(paths: Paths, _args: argparse.Namespace) -> int:
    indexed = build_index(paths.raw_dir, paths.index_path)
    for source in indexed:
        print(f"  {source.passages:3d} passages  {source.name}")
    print(f"Indexed {sum(s.passages for s in indexed)} passages from {len(indexed)} sources -> {paths.index_path}")
    return 0


def _cmd_search(paths: Paths, args: argparse.Namespace) -> int:
    if args.limit < 1:
        raise WikiError("--limit must be at least 1")
    results = search(paths.index_path, args.query, args.limit)
    print(f'Search (local index, no model): "{args.query}" -> {len(results)} passage(s)\n')
    for result in results:
        chunk = result.chunk
        print(f"[{result.rank}] {chunk.label}")
        print(f"    {chunk.chunk_id}, lines {chunk.start_line}-{chunk.end_line}, score {result.score:.2f}")
        print("    " + chunk.text.replace("\n", "\n    ") + "\n")
    if not results:
        print("No passage contains those words. Try different or fewer words.")
    return 0


def _make_model(args: argparse.Namespace) -> LanguageModel:
    return OllamaClient(base_url=args.ollama_url, model=args.model)


def _cmd_ingest(paths: Paths, args: argparse.Namespace) -> int:
    if args.raw is not None and args.raw.resolve() != paths.raw_dir.resolve():
        raise WikiError(f"Sources are read from {paths.raw_dir}; to use another folder, run with --root pointing at "
                        "a project whose vault/raw holds them.")
    plan = load_plan(paths.plan_path)
    model = _make_model(args)
    print(f"Ingesting {len(plan.concepts)} notes with {model.name} locally. This takes a while on a CPU; "
          "notes that are already up to date are skipped.", file=sys.stderr)
    report = ingest(plan, paths, model, only=args.only, force=args.force)
    counts: dict[str, int] = {}
    for outcome in report.outcomes:
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
        for note in outcome.dropped:
            print(f"    dropped from '{outcome.title}': {note}")
        if outcome.status in ("failed", "needs attention"):
            print(f"    {outcome.title}: {outcome.detail}", file=sys.stderr)
    if report.unplanned_sources:
        print(f"Note: these sources are indexed but not in the plan's source list: {', '.join(report.unplanned_sources)}")
    summary = ", ".join(f"{n} {status}" for status, n in sorted(counts.items()))
    print(f"Done in {report.seconds:.0f} s: {summary}. Indexed {report.indexed_passages} passages. "
          f"Updated {paths.vault_dir / 'index.md'} and the Source Catalog.")
    return 1 if counts.get("failed") else 0


def _cmd_approve(paths: Paths, args: argparse.Namespace) -> int:
    if not args.all and not args.titles:
        raise WikiError("Say which notes to approve (their titles) or use --all.")
    changed = approve(paths, None if args.all else args.titles)
    print(f"Marked {len(changed)} note(s) as reviewed." + (f" ({', '.join(changed)})" if changed and len(changed) <= 6 else ""))
    return 0


_CHAT_HELP = """\
  /notes <message>   force a notes lookup for this message
  /search <words>    show original passages (no model)
  /clear             forget the conversation so far
  /help              this list
  /exit              leave the chat
Anything else is sent to the assistant. It searches your notes only when the message needs them."""


def _chat_lines(script: Path | None):
    """Yield what the user types: from a script file, or from the keyboard until it is closed."""
    if script is not None:
        if not script.is_file():
            raise WikiError(f"Script file not found: {script}")
        for line in script.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                print(f"you> {line.strip()}")
                yield line.strip()
        return
    while True:
        try:
            yield input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return


def _print_turn_details(turn) -> None:
    print(f"  [{turn.route.reason}]")
    if turn.route.retrieve:
        cited = turn.report.cited if turn.report else ()
        used = [f"[{passage_label(r.rank)}] {r.chunk.label}" for r in turn.route.results if passage_label(r.rank) in cited]
        print(f"  [notes cited: {'; '.join(used) if used else 'none'}]")
        if turn.report and turn.report.status != "ok":
            print(f"  [citation check: {turn.report.describe()}]")
    else:
        print("  [no notes were searched or cited for this reply]")
    print(f"  [{turn.seconds:.1f} s]")


def _cmd_chat(paths: Paths, args: argparse.Namespace) -> int:
    model = _make_model(args)
    session = ChatSession(model, paths)
    session.system_prompt()  # fail early, before any typing, if persona.md is missing
    print(f"Chat (mode: local | model: {model.name} | assistant: Scout). /help for commands, /exit to leave.")
    for line in _chat_lines(args.script):
        if not line:
            continue
        if line in ("/exit", "/quit"):
            break
        if line == "/help":
            print(_CHAT_HELP)
        elif line == "/clear":
            session.clear()
            print("(conversation cleared)")
        elif line.startswith("/search"):
            _cmd_search(paths, argparse.Namespace(query=line[7:].strip(), limit=DEFAULT_LIMIT))
        elif line.startswith("/") and not line.startswith("/notes "):
            print(f"Unknown command {line.split()[0]}. Type /help.")
        else:
            force = line.startswith("/notes ")
            print("scout> ", end="", flush=True)
            try:
                turn = session.say(line[7:].strip() if force else line,
                                   on_token=lambda piece: print(piece, end="", flush=True), force_notes=force)
            except ModelError as error:  # a stopped model server must not end the whole session
                print(f"\n  [{error}]")
                continue
            print()
            _print_turn_details(turn)
    return 0


def _cmd_ask(paths: Paths, args: argparse.Namespace) -> int:
    if args.top_k < 1:
        raise WikiError("--top-k must be at least 1")
    model = _make_model(args)
    print(f"Asking {model.name} locally (this can take a few seconds)...", file=sys.stderr)
    try:
        result = answer_question(args.question, paths.index_path, model, paths.prompts_dir, args.top_k)
    except ModelError as error:
        raise WikiError(f"{error} (`wiki search` works without the model if you only need the passages.)") from error
    print(format_result(result, model.name))
    if not args.no_log:
        save_run(paths.log_dir / "ask.jsonl", result)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Passages contain characters (curly quotes, dashes) that a Windows console may not encode.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    paths = Paths(args.root or default_root())
    try:
        return args.handler(paths, args)
    except WikiError as error:
        print(f"wiki: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
