from pathlib import Path

import pytest

from wiki.chunk import Chunk
from wiki.prompts import load_instructions
from wiki.retrieval import SearchResult
from wiki.verify import check_answerable, seeks_specific_fact, verify_answer


@pytest.fixture
def prompts(tmp_path):
    (tmp_path / "verify-instructions.md").write_text("Reply YES or NO.")
    (tmp_path / "answerable-instructions.md").write_text("Reply KIND and VERDICT.")
    return tmp_path


def passage(rank=1, text="The exam is 40% of the grade."):
    return SearchResult(rank, 1.0, Chunk("Data.md", "Lecture 1", rank, text, 1, 2))


@pytest.mark.parametrize("reply, supported", [
    ("YES", True), ("Yes.", True), ("yes, it does", True), ("**YES**", True), ("  YES\n", True),
    ("NO", False), ("No, the passages only give a weight.", False), ("", False),
    ("Maybe", False), ("I think yes", False), ("YESTERDAY", False),
])
def test_only_a_clear_yes_counts(prompts, fake_model, reply, supported):
    verdict = verify_answer(fake_model(reply), prompts, "When is the exam?", "It is 40%.", [passage()])
    assert verdict.supported is supported and verdict.raw == reply


def test_prompt_has_question_answer_and_cited_passages_with_their_source(prompts, fake_model):
    model = fake_model("YES")
    verify_answer(model, prompts, "When is the exam?", "It is 40%.", [passage(2, "Only this passage.")])
    system, user = model.calls[0]
    assert system["content"] == "Reply YES or NO."
    for part in ("Question: When is the exam?", "Proposed answer: It is 40%.", 'source="Data.md"', "Only this passage."):
        assert part in user["content"]


def test_verification_is_deterministic_and_short(prompts, fake_model):
    model = fake_model("YES")
    verify_answer(model, prompts, "q", "a", [passage()])
    assert model.settings[0] == {"temperature": 0.0, "max_tokens": 8, "seed": 0}


def test_the_shipped_verifier_instructions_name_the_failure_modes():
    text = load_instructions(Path(__file__).resolve().parents[1] / "prompts", "verify-instructions.md")
    for must_have in ("YES", "NO", "different kind of fact", "different course"):
        assert must_have in text


def test_the_shipped_answerability_instructions_ask_for_kind_then_verdict():
    text = load_instructions(Path(__file__).resolve().parents[1] / "prompts", "answerable-instructions.md")
    for must_have in ("KIND:", "VERDICT:", "a date", "grade weight"):
        assert must_have in text


@pytest.mark.parametrize("reply, supported", [
    ("KIND: date | VERDICT: NO", False),
    ("KIND: number | VERDICT: YES", True),
    ("kind: reason | verdict: yes", True),
    ("KIND: a date | VERDICT: **NO**", False),
    ("VERDICT: YES", True),
    ("YES", False),  # not in the requested format: fail closed
    ("KIND: date", False),
    ("", False),
])
def test_answerability_reads_only_the_verdict_field(prompts, fake_model, reply, supported):
    verdict = check_answerable(fake_model(reply), prompts, "When is it?", [passage()])
    assert verdict.supported is supported and verdict.raw == reply


def test_answerability_prompt_has_no_draft_answer_and_is_deterministic(prompts, fake_model):
    model = fake_model("KIND: date | VERDICT: NO")
    check_answerable(model, prompts, "When is the exam?", [passage(1, "Only this passage.")])
    system, user = model.calls[0]
    assert system["content"] == "Reply KIND and VERDICT."
    assert "Proposed answer" not in user["content"] and "Only this passage." in user["content"]
    assert model.settings[0] == {"temperature": 0.0, "max_tokens": 40, "seed": 0}


@pytest.mark.parametrize("question", [
    "When is the MBA 201A final exam?", "Where is the workshop?", "Who wrote the report?",
    "How many batches should the bakery bake?", "How much does a two-part tariff earn?", "how long is the exam",
    "What sample size guarantees a margin of error of plus or minus 3 percentage points?",
    "What is the weight of the final exam in the grade?", "What date is the deadline?", "Which lecture covers monopoly?",
])
def test_fact_seeking_questions_are_recognised(question):
    assert seeks_specific_fact(question)


@pytest.mark.parametrize("question", [
    "Why can't a monopolist just keep producing until price equals marginal cost?",
    "What three conditions must hold for group pricing, and how does the Netflix example satisfy them?",
    "What is the golden rule for a price-taking firm?", "Explain how versioning works.",
    "How does the Netflix example satisfy them?", "Describe the shutdown decision", "What is opportunity cost?",
])
def test_open_ended_questions_are_not_treated_as_fact_seeking(question):
    assert not seeks_specific_fact(question)
