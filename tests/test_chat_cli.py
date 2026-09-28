import pytest

from wiki.cli import main
from wiki.errors import ModelError


@pytest.fixture
def project(tmp_path):
    raw = tmp_path / "vault" / "raw"
    raw.mkdir(parents=True)
    (raw / "Economics.md").write_text(
        "## Lecture 5: Monopoly\n\nA monopolist sets marginal revenue equal to marginal cost.\n", encoding="utf-8")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "persona.md").write_text("You are Scout.", encoding="utf-8")
    main(["--root", str(tmp_path), "index"])
    return tmp_path


def chat(project, capsys, script_text, tmp_path_factory=None):
    script = project / "script.txt"
    script.write_text(script_text, encoding="utf-8")
    code = main(["--root", str(project), "chat", "--script", str(script)])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_scripted_chat_shows_the_transcript_the_route_and_no_citations_for_conversation(project, capsys, monkeypatch, fake_model):
    model = fake_model("I can brainstorm, draft and plan with you.")
    monkeypatch.setattr("wiki.cli._make_model", lambda args: model)
    code, out, _ = chat(project, capsys, "what can you help me with?\n/exit\nthis line is never sent\n")
    assert code == 0 and len(model.calls) == 1
    assert "Chat (mode: local | model: fake:1b | assistant: Scout)" in out
    assert "you> what can you help me with?" in out and "scout> I can brainstorm, draft and plan with you." in out
    assert "[conversation: a question about the assistant itself]" in out
    assert "[no notes were searched or cited for this reply]" in out


def test_a_notes_turn_reports_which_notes_were_cited(project, capsys, monkeypatch, fake_model):
    model = fake_model("A monopolist sets marginal revenue equal to marginal cost [S1].")
    monkeypatch.setattr("wiki.cli._make_model", lambda args: model)
    _, out, _ = chat(project, capsys, "/notes monopolist marginal revenue\n")
    assert "[notes cited: [S1] Economics.md > Lecture 5: Monopoly]" in out and "you asked for the notes" in out


def test_follow_up_in_a_scripted_chat_uses_the_conversation(project, capsys, monkeypatch, fake_model):
    model = fake_model("A long draft of a plan.", "A short plan.")
    monkeypatch.setattr("wiki.cli._make_model", lambda args: model)
    _, out, _ = chat(project, capsys, "Draft a study plan for my final\nmake that shorter\n")
    assert "[conversation: a drafting, planning or brainstorming request]" in out
    assert "[conversation: a follow-up on the previous reply]" in out
    assert model.calls[1][2]["content"] == "A long draft of a plan."


def test_search_command_inside_chat_needs_no_model(project, capsys, monkeypatch, fake_model):
    model = fake_model()
    monkeypatch.setattr("wiki.cli._make_model", lambda args: model)
    _, out, _ = chat(project, capsys, "/search monopolist\n")
    assert "Search (local index, no model)" in out and "A monopolist sets marginal revenue" in out and model.calls == []


def test_help_clear_and_unknown_commands(project, capsys, monkeypatch, fake_model):
    monkeypatch.setattr("wiki.cli._make_model", lambda args: fake_model())
    _, out, _ = chat(project, capsys, "/help\n/clear\n/dance\n")
    assert "/notes <message>" in out and "(conversation cleared)" in out and "Unknown command /dance" in out


def test_a_model_that_stops_mid_chat_does_not_end_the_session(project, capsys, monkeypatch, fake_model):
    class Flaky:
        name = "flaky:1b"
        calls = 0

        def identity(self):
            return {}

        def chat(self, messages, *, temperature, max_tokens, seed=None, response_format=None, on_token=None):
            from wiki.llm import Reply
            Flaky.calls += 1
            if Flaky.calls == 1:
                raise ModelError("Cannot reach the local model server at http://127.0.0.1:11434. Start it with: ollama serve")
            if on_token:
                on_token("Back again.")
            return Reply("Back again.", self.name, 1, 1, 0.1, 0.0)

    monkeypatch.setattr("wiki.cli._make_model", lambda args: Flaky())
    code, out, _ = chat(project, capsys, "Draft something\nDraft something else\n")
    assert code == 0 and "ollama serve" in out and "scout> Back again." in out


def test_missing_script_or_persona_are_friendly_errors(project, capsys, monkeypatch, fake_model):
    monkeypatch.setattr("wiki.cli._make_model", lambda args: fake_model())
    code = main(["--root", str(project), "chat", "--script", str(project / "nope.txt")])
    assert code == 1 and "Script file not found" in capsys.readouterr().err
    (project / "prompts" / "persona.md").unlink()
    code = main(["--root", str(project), "chat", "--script", str(project / "script.txt")])
    assert code == 1 and "Cannot read the instruction file" in capsys.readouterr().err


def test_chat_refuses_a_non_local_model_address(project, capsys):
    code = main(["--root", str(project), "chat", "--ollama-url", "https://api.example.com"])
    assert code == 1 and "not a local address" in capsys.readouterr().err
