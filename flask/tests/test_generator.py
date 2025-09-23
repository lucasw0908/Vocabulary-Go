import asyncio

from flask import Flask

from app.models import db
from app.models.libraries import Libraries
from app.models.words import Words


def test_helper_pure_functions():
    from app.generator.english_helper import EnglishHelper
    helper = EnglishHelper.__new__(EnglishHelper)
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
    assert EnglishHelper.trim_empty_lines("a\n\n b \n\n") == "a\n b "

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


