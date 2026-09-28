from pathlib import Path

import pytest

from wiki import router
from wiki.chunk import Chunk
from wiki.errors import WikiError
from wiki.retrieval import SearchResult
from wiki.router import decide_route

INDEX = Path("unused.db")


def stub_search(monkeypatch, score=6.0, results=True, error=None):
    """Replace the real search so tests decide the score. Returns the list of queries that were searched."""
    calls = []

    def fake(index_path, text, limit=5, sources=None):
        calls.append(text)
        if error:
            raise error
        return [SearchResult(1, score, Chunk("Notes.md", "Lecture 1", 1, "passage text", 1, 2))] if results else []

    monkeypatch.setattr(router, "search", fake)
    return calls


@pytest.mark.parametrize("message", [
    "hi there!", "Hello", "thanks, that was useful", "ok cool", "good morning",
    "what can you help me with?", "what can we do?", "What can you do?", "who are you?", "help", "How does this work?",
    "what are your commands?", "What can I ask?",
    "Draft a three-day study plan for my data and decisions final",
    "Help me brainstorm names for a study group", "Write a short email to my group asking to meet on Friday",
    "I feel stressed about the exam, any advice?", "Give me some ideas for a group project", "please plan my week",
    "Can you help me prepare for the midterm?", "Compose a message to my professor",
])
def test_conversation_never_searches_the_notes(monkeypatch, message):
    calls = stub_search(monkeypatch)
    route = decide_route(message, INDEX)
    assert not route.retrieve and route.results == () and calls == []
    assert route.reason.startswith("conversation")


@pytest.mark.parametrize("message", [
    "make that shorter", "Could you make it shorter?", "rewrite it in bullet points", "can you simplify that?",
    "translate that into Spanish", "expand on the second point", "try again", "more formal please",
])
def test_follow_ups_use_the_conversation_not_the_notes(monkeypatch, message):
    calls = stub_search(monkeypatch)
    route = decide_route(message, INDEX, has_history=True)
    assert not route.retrieve and calls == [] and "follow-up" in route.reason


def test_a_follow_up_phrase_without_any_history_is_still_not_a_notes_lookup(monkeypatch):
    calls = stub_search(monkeypatch)
    assert not decide_route("make that shorter", INDEX, has_history=False).retrieve and calls == []


@pytest.mark.parametrize("message", [
    "explain marginal revenue", "what is opportunity cost?", "how do I interpret the slope in a regression?",
    "why do firms use bundling?", "compare sampling bias and survivorship bias", "Define standard error",
])
def test_questions_about_course_content_search_and_retrieve_when_the_match_is_decent(monkeypatch, message):
    calls = stub_search(monkeypatch, score=5.5)
    route = decide_route(message, INDEX)
    assert route.retrieve and len(route.results) == 1 and calls == [message]
    assert "course content" in route.reason and "5.5" in route.reason


def test_a_content_question_with_only_a_weak_match_is_treated_as_conversation(monkeypatch):
    stub_search(monkeypatch, score=1.9)
    route = decide_route("what is the weather like in Berkeley today?", INDEX)
    assert not route.retrieve and "too weak" in route.reason


def test_a_content_question_with_no_match_at_all_is_treated_as_conversation(monkeypatch):
    stub_search(monkeypatch, results=False)
    route = decide_route("what is the capital of France?", INDEX)
    assert not route.retrieve and "nothing matched" in route.reason


@pytest.mark.parametrize("message", [
    "summarize my notes on regression", "what did the lecture say about type I errors?", "According to my notes, what is a sunk cost?",
    "Draft a study plan using my notes", "in lecture 5 what was the bakery example", "look in the wiki for menu pricing",
    "summarize my notes again",
])
def test_mentioning_the_notes_always_searches_even_with_a_modest_match(monkeypatch, message):
    calls = stub_search(monkeypatch, score=2.0)
    route = decide_route(message, INDEX, has_history=True)
    assert route.retrieve and calls == [message] and "referred to your notes" in route.reason


def test_the_notes_command_forces_a_lookup_for_any_message(monkeypatch):
    calls = stub_search(monkeypatch, score=0.5)
    route = decide_route("hi", INDEX, force_notes=True)
    assert route.retrieve and calls == ["hi"] and "/notes" in route.reason


def test_a_message_without_searchable_words_falls_back_to_conversation(monkeypatch):
    stub_search(monkeypatch, error=WikiError("Nothing to search for: use at least one meaningful word"))
    assert not decide_route("what is the", INDEX, force_notes=True).retrieve


def test_other_search_errors_are_not_swallowed(monkeypatch):
    stub_search(monkeypatch, error=WikiError("No search index at data/index.db. Build it first with: wiki index"))
    with pytest.raises(WikiError, match="wiki index"):
        decide_route("explain marginal revenue", INDEX)


def test_plain_statements_are_conversation(monkeypatch):
    calls = stub_search(monkeypatch)
    route = decide_route("I have my final on Friday", INDEX)
    assert not route.retrieve and calls == []
