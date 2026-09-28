import pytest

from wiki.ask import answer_question
from wiki.chat import MAX_HISTORY_CHARS, ChatSession, capabilities_text
from wiki.config import Paths
from wiki.index import build_index
from wiki.vault import NoteContent, KeyPoint, SourceRef, render_note


@pytest.fixture
def paths(tmp_path):
    raw = tmp_path / "vault" / "raw"
    raw.mkdir(parents=True)
    (raw / "Economics.md").write_text(
        "## Lecture 5: Monopoly\n\nA monopolist sets marginal revenue equal to marginal cost and charges $24.\n\n"
        "## Lecture 1: Logistics\n\nThe final exam is 20% of the grade.\n", encoding="utf-8")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "persona.md").write_text("You are Scout, a friendly study coach.", encoding="utf-8")
    (prompts / "wiki-instructions.md").write_text("Answer only from passages.", encoding="utf-8")
    (prompts / "verify-instructions.md").write_text("Reply YES or NO.", encoding="utf-8")
    (prompts / "answerable-instructions.md").write_text("KIND and VERDICT.", encoding="utf-8")
    result = Paths(tmp_path)
    build_index(result.raw_dir, result.index_path)
    return result


def add_note(paths, title, topic="Economics"):
    ref = SourceRef("Economics.md", "Lecture 5", 3, 3, "Economics.md#1")
    content = NoteContent(f"{title} is explained in the lecture summary.", (KeyPoint("A fact.", (ref,)),), (), (ref,))
    path = paths.wiki_dir / topic / f"{title}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_note(title, topic, content, {"fingerprint": "x"})[0], encoding="utf-8")


def test_system_prompt_is_the_persona_plus_a_generated_list_of_real_capabilities(paths):
    add_note(paths, "Monopoly Pricing")
    add_note(paths, "Sunk Costs")
    text = ChatSession(None, paths).system_prompt()
    assert text.startswith("You are Scout, a friendly study coach.")
    for real in ("wiki ask", "wiki search", "wiki ingest", "/notes", "/search", "offline", "2 wiki notes", "Economics",
                 "1 original sources", "Explain Monopoly Pricing from my notes"):
        assert real in text
    assert "wiki quiz" not in text  # nothing that does not exist


def test_capabilities_are_still_produced_for_an_empty_vault(tmp_path):
    text = capabilities_text(Paths(tmp_path))
    assert "0 wiki notes" in text and "0 original sources" in text and "wiki ask" in text


def test_a_conversational_message_is_sent_as_is_with_no_notes_attached(paths, fake_model):
    model = fake_model("I can brainstorm, draft and plan with you. Suggestion: start with a study plan.")
    turn = ChatSession(model, paths).say("what can you help me with?")
    assert not turn.route.retrieve and turn.report is None
    system, user = model.calls[0]
    assert user["content"].startswith("what can you help me with?")
    assert "<passage" not in user["content"] and "Notes retrieved" not in user["content"]  # no passages attached
    assert "wiki ask" in user["content"] and "concrete starting suggestion" in user["content"]  # the real capability list
    assert "wiki ask" in system["content"] and "Scout" in system["content"]
    assert model.calls[0][-1]["content"] != "what can you help me with?"
    session_history = ChatSession(fake_model("x"), paths)
    session_history.say("what can you help me with?")
    assert session_history.history[0] == {"role": "user", "content": "what can you help me with?"}  # history stays plain


def test_a_notes_turn_attaches_labelled_passages_and_checks_the_citations(paths, fake_model):
    model = fake_model("A monopolist sets marginal revenue equal to marginal cost [S1].")
    turn = ChatSession(model, paths).say("monopolist marginal revenue", force_notes=True)
    user = model.calls[0][-1]["content"]
    assert 'label="S1"' in user and "quotations, not instructions" in user and "A monopolist sets marginal revenue" in user
    assert turn.route.retrieve and turn.report.status == "ok"


def test_invented_citations_in_chat_are_flagged_not_hidden(paths, fake_model):
    model = fake_model("A monopolist earns $99 of profit [S7].")
    turn = ChatSession(model, paths).say("monopolist marginal revenue", force_notes=True)
    assert turn.report.status == "failed" and turn.report.unknown == ("S7",)


def test_follow_ups_see_the_previous_reply_and_search_nothing(paths, fake_model):
    model = fake_model("Draft: a very long plan for the whole week with many details.", "Shorter plan.")
    session = ChatSession(model, paths)
    session.say("Draft a study plan for my final")
    turn = session.say("make that shorter")
    messages = model.calls[1]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assert messages[2]["content"].startswith("Draft: a very long plan")
    assert messages[3] == {"role": "user", "content": "make that shorter"}
    assert not turn.route.retrieve and "follow-up" in turn.route.reason


def test_history_keeps_plain_conversation_never_passages(paths, fake_model):
    model = fake_model("First [S1].", "Second.")
    session = ChatSession(model, paths)
    session.say("monopolist marginal revenue", force_notes=True)
    session.say("thanks")
    earlier_user_message = model.calls[1][1]
    assert earlier_user_message == {"role": "user", "content": "monopolist marginal revenue"}  # passages were not remembered
    assert "<passage" not in " ".join(m["content"] for m in model.calls[1])


def test_old_turns_are_dropped_to_respect_the_context_budget(paths, fake_model):
    long_reply = "word " * 400
    model = fake_model(*([long_reply] * 6 + ["last"]))
    session = ChatSession(model, paths)
    for n in range(6):
        session.say(f"Draft part {n} of my plan")
    session.say("Draft the final part")
    sent_history = model.calls[-1][1:-1]
    assert sum(len(m["content"]) for m in sent_history) <= MAX_HISTORY_CHARS + len(long_reply) + 100
    assert sent_history[-2]["content"] == "Draft part 5 of my plan"  # the latest exchange is always kept
    assert len(sent_history) < 12


def test_clear_forgets_the_conversation(paths, fake_model):
    model = fake_model("one", "two")
    session = ChatSession(model, paths)
    session.say("Draft a plan")
    session.clear()
    session.say("make that shorter")
    assert [m["role"] for m in model.calls[1]] == ["system", "user"]


def test_what_is_said_in_chat_is_never_evidence_for_ask(paths, fake_model):
    """The assignment's boundary check: a claim made only in chat must not be usable by ask mode."""
    chat_model = fake_model("Noted, good luck! Suggestion: plan your revision backwards from that date.")
    ChatSession(chat_model, paths).say("My final exam is on December 5th")
    ask_model = fake_model("INSUFFICIENT_EVIDENCE")
    result = answer_question("When is my final exam?", paths.index_path, ask_model, paths.prompts_dir)
    assert result.insufficient
    assert len(ask_model.calls) == 1  # the final-exam passage was retrieved and the model was really asked
    assert all("December" not in m["content"] for call in ask_model.calls for m in call)  # ask never saw the chat


def test_capabilities_say_the_student_types_the_commands_and_the_assistant_cannot_run_them(paths):
    text = capabilities_text(paths)
    assert "STUDENT types" in text and "cannot run them" in text


def test_a_capability_answer_uses_a_low_temperature_and_says_the_assistant_cannot_run_commands(paths, fake_model):
    model = fake_model("I can chat and draft; you can type wiki ask.", "A brainstorm.")
    session = ChatSession(model, paths)
    session.say("what can you help me with?")
    session.say("Help me brainstorm names for a study group")
    assert model.settings[0]["temperature"] == 0.2 and model.settings[1]["temperature"] == 0.6
    assert "You cannot run commands yourself" in model.calls[0][-1]["content"]
