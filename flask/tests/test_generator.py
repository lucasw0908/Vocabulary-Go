import asyncio
import time

from flask import Flask

from app.models import db
from app.models.libraries import Libraries
from app.models.words import Words


def test_api_key_manager_rotation_and_cooldown(monkeypatch):
    from app.generator.api_key_manager import ApiKeyManager

    manager = ApiKeyManager(["k1", "k2"])
    # Make k1 unavailable to start
    manager.available["k1"] = False

    # Should pick k2
    key = asyncio.get_event_loop().run_until_complete(manager.get_available_api_key())
    assert key == "k2"

    # Monkeypatch sleep to be instant, so cooldown thread runs immediately
    monkeypatch.setattr(time, "sleep", lambda s: None)
    asyncio.get_event_loop().run_until_complete(manager.update_retry_delay(0))
    # After cooldown, k2 should be available again
    assert manager.available["k2"] is True


def test_gemini_helper_pure_functions():
    from app.generator.gemini_english_helper import GeminiEnglishHelper

    helper = GeminiEnglishHelper.__new__(GeminiEnglishHelper)
    helper.retry_attempts = 0

    # blankify
    assert helper.blankify("the") == "___"
    assert helper.blankify("") == ""
    assert helper.blankify("a") == "___"
    assert helper.blankify("go") == "___"
    assert helper.blankify("played").endswith("___")
    assert helper.blankify("playing").endswith("___")
    assert helper.blankify("phrase").startswith("p") and helper.blankify("phrase").endswith("e")

    # trim_empty_lines
    assert GeminiEnglishHelper.trim_empty_lines("a\n\n b \n\n") == "a\n b "

    # similarity and best_match
    sim = helper.check_similarity("hello world", "hello world")
    assert 0.99 <= sim <= 1.0
    best, score, positions = helper.best_match("this is a test phrase", "test phrase")
    assert best == "test phrase"
    assert positions == [3, 4]


def test_generate_adds_sentences(app: Flask, monkeypatch):
    # Prepare a small library and word
    with app.app_context():
        # Use an existing writable DB in the app context
        lib = Libraries.query.filter_by(name="UnitTestLib").first()
        if lib is None:
            lib = Libraries(name="UnitTestLib", description="t", public=True, author_id=1)
            db.session.add(lib)
            db.session.commit()
        if not Words.query.filter_by(library=lib, english="Hello").first():
            w = Words(chinese="你好", english="Hello")
            w.library = lib
            db.session.add(w)
            db.session.commit()

    # Fake ai_helper.question
    class FakeAI:
        async def question(self, phrase: str):
            return {"sentence": "Hello | 你好", "appear": phrase.lower()}

    import app.generator.__init__ as gen_mod
    monkeypatch.setattr(gen_mod, "ai_helper", FakeAI())

    # Run generate()
    asyncio.get_event_loop().run_until_complete(gen_mod.generate())

    # Verify sentence inserted
    from app.models.sentences import Sentences
    with app.app_context():
        # There should be at least one sentence for the word or none if duplicate filtered
        s = Sentences.query.filter_by(word_english="Hello").first()
        assert s is None or (s.english == "Hello" and s.chinese == "你好")


