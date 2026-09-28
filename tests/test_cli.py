import pytest

from wiki.cli import main


@pytest.fixture
def project(tmp_path):
    """A project folder with one source. Returns the root path."""
    raw = tmp_path / "vault" / "raw"
    raw.mkdir(parents=True)
    (raw / "Notes.md").write_text("## Lecture 1: Markets\n\nPrices reach equilibrium where supply meets demand.\n")
    return tmp_path


def run(project, capsys, *args):
    code = main(["--root", str(project), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_index_then_search_shows_original_passage_and_location(project, capsys):
    code, out, _ = run(project, capsys, "index")
    assert code == 0 and "Indexed 1 passages from 1 sources" in out

    code, out, err = run(project, capsys, "search", "equilibrium demand")
    assert code == 0 and err == ""
    assert "[1] Notes.md > Lecture 1: Markets" in out
    assert "Prices reach equilibrium where supply meets demand." in out
    assert "no model" in out  # search says it does not use the language model


def test_search_without_index_is_a_friendly_error_not_a_traceback(project, capsys):
    code, out, err = run(project, capsys, "search", "equilibrium")
    assert code == 1 and out == ""
    assert err.startswith("wiki: No search index") and "Traceback" not in err


def test_search_with_no_matches_says_so(project, capsys):
    run(project, capsys, "index")
    code, out, _ = run(project, capsys, "search", "penguin")
    assert code == 0 and "No passage contains those words" in out


def test_meaningless_query_is_a_friendly_error(project, capsys):
    run(project, capsys, "index")
    code, _, err = run(project, capsys, "search", "what is the")
    assert code == 1 and "meaningful word" in err


def test_limit_must_be_positive(project, capsys):
    run(project, capsys, "index")
    code, _, err = run(project, capsys, "search", "equilibrium", "--limit", "0")
    assert code == 1 and "--limit" in err


def test_index_reports_a_missing_source_folder(tmp_path, capsys):
    code, _, err = run(tmp_path, capsys, "index")
    assert code == 1 and "Source folder not found" in err


@pytest.fixture
def asking_project(project):
    prompts = project / "prompts"
    prompts.mkdir()
    (prompts / "wiki-instructions.md").write_text("Answer only from passages.")
    (prompts / "verify-instructions.md").write_text("Reply YES or NO.")
    (prompts / "answerable-instructions.md").write_text("KIND and VERDICT.")
    main(["--root", str(project), "index"])
    return project


def test_ask_prints_answer_citations_and_saves_a_log(asking_project, capsys, monkeypatch, fake_model):
    model = fake_model("Prices reach equilibrium where supply meets demand [S1].", "YES")
    monkeypatch.setattr("wiki.cli._make_model", lambda args: model)
    capsys.readouterr()
    code, out, err = run(asking_project, capsys, "ask", "Explain how prices reach equilibrium")
    assert code == 0
    assert "mode: local | model: fake:1b" in out and "Citation check: OK" in out and "Verification:" in out
    assert "Asking fake:1b locally" in err  # progress goes to stderr, the answer to stdout
    assert (asking_project / "data" / "logs" / "ask.jsonl").is_file()


def test_ask_no_log_flag_writes_nothing(asking_project, capsys, monkeypatch, fake_model):
    monkeypatch.setattr("wiki.cli._make_model", lambda args: fake_model("Prices [S1].", "YES"))
    run(asking_project, capsys, "ask", "equilibrium prices", "--no-log")
    assert not (asking_project / "data" / "logs").exists()


def test_ask_with_the_model_server_down_explains_and_points_to_search(asking_project, capsys):
    port_closed_url = "http://127.0.0.1:1"
    code, _, err = run(asking_project, capsys, "ask", "equilibrium", "--ollama-url", port_closed_url)
    assert code == 1 and "ollama serve" in err and "wiki search" in err and "Traceback" not in err


def test_ask_refuses_a_non_local_model_address(asking_project, capsys):
    code, _, err = run(asking_project, capsys, "ask", "equilibrium", "--ollama-url", "https://api.example.com")
    assert code == 1 and "not a local address" in err


def test_ask_without_index_is_a_friendly_error(project, capsys, monkeypatch, fake_model):
    (project / "prompts").mkdir()
    (project / "prompts" / "wiki-instructions.md").write_text("rules")
    monkeypatch.setattr("wiki.cli._make_model", lambda args: fake_model())
    code, _, err = run(project, capsys, "ask", "equilibrium")
    assert code == 1 and "wiki index" in err


def test_ask_only_offers_local_mode(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["ask", "q", "--mode", "online"])
    assert exit_info.value.code == 2


def test_help_lists_the_commands(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert "search" in out and "index" in out and "offline" in out


def test_unknown_command_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["dance"])
    assert exit_info.value.code == 2
