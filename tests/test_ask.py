import json

import pytest

from wiki.ask import INSUFFICIENT_MESSAGE, answer_question, format_result, interpret_reply, save_run
from wiki.errors import WikiError
from wiki.index import build_index


@pytest.fixture
def project(tmp_path):
    """Indexed mini-vault plus instruction files. Returns (index_path, prompts_dir)."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "Stats.md").write_text(
        "## Lecture 5: Polling\n\nA plus-or-minus 3 percentage point poll needs 1,112 people.\n\n"
        "## Lecture 1: Logistics\n\nThe final exam is 40% of the grade.\n"
    )
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "wiki-instructions.md").write_text("RULES: answer only from passages.")
    (prompts / "verify-instructions.md").write_text("CHECK: reply YES or NO.")
    (prompts / "answerable-instructions.md").write_text("ANSWERABLE: KIND and VERDICT.")
    index_path = tmp_path / "data" / "index.db"
    build_index(raw, index_path)
    return index_path, prompts


def test_grounded_answer_passes_both_checks_and_the_prompt_holds_evidence_only(project, fake_model):
    index_path, prompts = project
    model = fake_model("You need 1,112 people [S1].", "KIND: number | VERDICT: YES", "YES")
    result = answer_question("What poll sample size gives 3 percentage points?", index_path, model, prompts)

    assert not result.insufficient and result.answer == "You need 1,112 people [S1]."
    assert result.report.status == "ok" and result.answerable.supported and result.verdict.supported
    assert len(model.calls) == 3  # answer, draft-free answerability check, draft-aware verification
    system, user = model.calls[0]
    assert system == {"role": "system", "content": "RULES: answer only from passages."}
    assert "1,112 people" in user["content"] and 'label="S1"' in user["content"]
    assert result.mode == "local" and result.identity == {"runtime": "fake", "model": "fake:1b"}


def test_verification_sees_only_the_cited_passages_and_is_deterministic(project, fake_model):
    index_path, prompts = project
    model = fake_model("You need 1,112 people [S1].", "YES")
    answer_question("poll sample size", index_path, model, prompts)
    verify_system, verify_user = model.calls[1]
    assert verify_system["content"] == "CHECK: reply YES or NO."
    assert "1,112 people" in verify_user["content"] and "final exam" not in verify_user["content"]
    assert model.settings[1]["temperature"] == 0.0


def test_each_question_is_independent_no_history_carries_over(project, fake_model):
    index_path, prompts = project
    model = fake_model("First [S1].", "YES", "Second [S1].", "YES")
    answer_question("poll sample size", index_path, model, prompts)
    answer_question("final exam grade", index_path, model, prompts)
    assert [len(call) for call in model.calls] == [2, 2, 2, 2]  # system + user every time, nothing accumulated
    second_question_prompt = model.calls[2][1]["content"]
    assert second_question_prompt.endswith("Question: final exam grade")
    assert "poll sample size" not in second_question_prompt


def test_insufficient_evidence_reply_is_shown_as_the_harness_own_fixed_statement(project, fake_model):
    index_path, prompts = project
    model = fake_model("INSUFFICIENT_EVIDENCE. The passages say the exam is 40% of the grade.")
    result = answer_question("When is the final exam?", index_path, model, prompts)
    assert result.insufficient and result.report is None and len(model.calls) == 1
    assert result.answer == INSUFFICIENT_MESSAGE  # the model's extra claim about "40%" is dropped


def test_refusal_lists_the_closest_passages_without_claiming_anything(project, fake_model):
    index_path, prompts = project
    model = fake_model("INSUFFICIENT_EVIDENCE")
    text = format_result(answer_question("When is the final exam?", index_path, model, prompts), model.name)
    assert "Insufficient evidence" in text
    assert "Closest passages found (none of them gives the requested information):" in text
    assert "Stats.md > Lecture 1: Logistics" in text


def test_no_matching_passages_means_no_model_call(project, fake_model):
    index_path, prompts = project
    model = fake_model()
    result = answer_question("penguin volcano", index_path, model, prompts)
    assert result.insufficient and result.reply is None and model.calls == []


def test_a_draft_the_verifier_rejects_is_withheld_not_shown(project, fake_model):
    index_path, prompts = project
    model = fake_model("The final exam is 40% of the grade [S1].", "NO")
    result = answer_question("Explain the final exam grading", index_path, model, prompts)
    assert result.insufficient and result.answer == INSUFFICIENT_MESSAGE
    assert result.withheld_draft == "The final exam is 40% of the grade [S1]."  # kept for the log only
    assert "verification step did not confirm" in result.withheld_reason
    assert "40%" not in format_result(result, model.name).split("Closest passages")[0].split("Answer:")[1]


def test_an_unclear_verifier_reply_fails_closed(project, fake_model):
    index_path, prompts = project
    result = answer_question("poll people", index_path, fake_model("1,112 people [S1].", "Hmm, maybe"), prompts)
    assert result.insufficient and result.withheld_draft is not None


def test_fact_seeking_question_is_withheld_by_the_draft_free_answerability_check(project, fake_model):
    """The run-3 failure: the draft's number matches a cited passage, but the passage is not a date."""
    index_path, prompts = project
    model = fake_model("The final exam is 40% of the grade [S1].", "KIND: date | VERDICT: NO")
    result = answer_question("When is the final exam?", index_path, model, prompts)
    assert result.insufficient and result.answer == INSUFFICIENT_MESSAGE
    assert result.withheld_draft == "The final exam is 40% of the grade [S1]."
    assert "answerability check" in result.withheld_reason
    assert len(model.calls) == 2 and result.verdict is None  # the draft-aware verifier never got to be anchored


def test_answerability_check_never_sees_the_draft_answer(project, fake_model):
    index_path, prompts = project
    model = fake_model("The final exam is 40% of the grade [S1].", "KIND: date | VERDICT: NO")
    answer_question("When is the final exam?", index_path, model, prompts)
    system, user = model.calls[1]
    assert system["content"] == "ANSWERABLE: KIND and VERDICT."
    assert "Proposed answer" not in user["content"]


def test_an_unclear_answerability_reply_fails_closed(project, fake_model):
    index_path, prompts = project
    model = fake_model("The final exam is 40% of the grade [S1].", "probably yes")
    assert answer_question("When is the final exam?", index_path, model, prompts).insufficient


def test_non_fact_questions_skip_the_answerability_check(project, fake_model):
    index_path, prompts = project
    model = fake_model("Grading uses a final exam worth 40% [S1].", "YES")
    result = answer_question("Explain the final exam grading", index_path, model, prompts)
    assert result.answerable is None and not result.insufficient and len(model.calls) == 2


def test_invented_date_is_withheld_by_the_citation_check_without_a_second_call(project, fake_model):
    index_path, prompts = project
    model = fake_model("The final exam is on December 12 [S1].")
    result = answer_question("When is the final exam?", index_path, model, prompts)
    assert result.insufficient and "December" in result.withheld_reason and len(model.calls) == 1


def test_answer_without_citations_is_withheld(project, fake_model):
    index_path, prompts = project
    model = fake_model("It is 40% of the grade.")
    result = answer_question("final exam", index_path, model, prompts)
    assert result.insufficient and "cites no passage" in result.withheld_reason


def test_model_errors_propagate_as_wiki_errors(project):
    index_path, prompts = project

    class Broken:
        name = "broken"

        def chat(self, *args, **kwargs):
            raise WikiError("Cannot reach the local model server")

        def identity(self):
            return {}

    with pytest.raises(WikiError, match="Cannot reach"):
        answer_question("final exam", index_path, Broken(), prompts)


@pytest.mark.parametrize("raw, refused", [
    ("Plain answer [S1].", False),
    ("INSUFFICIENT_EVIDENCE", True),
    ("insufficient_evidence: not covered", True),
    ("Some invented answer. INSUFFICIENT_EVIDENCE", True),
])
def test_interpret_reply(raw, refused):
    flag, draft = interpret_reply(raw)
    assert flag is refused
    assert draft == ("" if refused else raw)  # nothing the model wrote survives a refusal


def test_result_display_names_mode_model_citations_verification_and_timing(project, fake_model):
    index_path, prompts = project
    model = fake_model("You need 1,112 people [S1].", "YES")
    text = format_result(answer_question("poll 3 percentage points", index_path, model, prompts), model.name)
    assert "mode: local | model: fake:1b | standalone: no chat history, no persona" in text
    assert "[S1] Stats.md > Lecture 5: Polling" in text and "Citation check: OK" in text
    assert "Verification:" in text and "Time: retrieval" in text and "characters sent" in text


def test_runs_are_appended_to_a_json_lines_log_including_withheld_drafts(project, fake_model, tmp_path):
    index_path, prompts = project
    log = tmp_path / "logs" / "ask.jsonl"
    save_run(log, answer_question("poll people", index_path, fake_model("A [S1].", "YES"), prompts))
    save_run(log, answer_question("final exam", index_path, fake_model("B is 40% [S1].", "NO"), prompts))
    first, second = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert first["answer"] == "A [S1]." and first["verification"]["supported"] is True
    assert first["mode"] == "local" and first["model"]["model"] == "fake:1b"
    assert first["retrieved"][0]["label"] == "S1" and "text" in first["retrieved"][0]
    assert second["insufficient"] is True and second["withheld_draft"] == "B is 40% [S1]."
