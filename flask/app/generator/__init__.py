import asyncio
import random
import threading
import logging

from sqlalchemy.orm import scoped_session, sessionmaker

from ..config import GEMENI_APIKEYS, API_GENERATION_DURATION, API_MODEL_NAME, API_RETRY_ATTEMPTS, API_RETRY_DELAY
from ..models import db
from ..models.words import Words
from ..models.sentences import Sentences
from ..models.libraries import Libraries
from .gemini_english_helper import GeminiEnglishHelper
from .api_key_manager import ApiKeyManager


log = logging.getLogger(__name__)
ai_helper = GeminiEnglishHelper(
    ApiKeyManager(GEMENI_APIKEYS),
    model_name=API_MODEL_NAME,
    max_retry_attempts=API_RETRY_ATTEMPTS,
    retry_delay=API_RETRY_DELAY
)


async def generate() -> None:
    
    session = scoped_session(sessionmaker(bind=db.engine), scopefunc=threading.get_ident)
    
    libraries: list[Libraries] = session.query(Libraries).all()
    
    for library in libraries:
        
        words: list[Words] = session.query(Words).filter_by(library=library).all()
        random.shuffle(words)

        for word in words:
            question = await ai_helper.question(word.english)
            
            if question is None:
                log.error(f"Failed to generate question for word: {word.english}, skipping...")
                continue
            
            s_english, s_chinese = map(str.strip, question["sentence"].split("|", 1))
            
            db.session.add(Sentences(
                chinese=s_chinese,
                english=s_english,
                word_chinese=word.chinese,
                word_english=word.english
            ))

            db.session.commit()


def init_generator() -> None:
    
    async def _generate() -> None:
        while True:
            await generate()
            log.info(f"Questions generated successfully, waiting for the next interval...({API_GENERATION_DURATION} seconds)")
            await asyncio.sleep(API_GENERATION_DURATION)
            
    def _start_event_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()
        
    _loop = asyncio.new_event_loop()

    t = threading.Thread(target=_start_event_loop, args=(_loop,), daemon=True)
    t.start()
    
    _loop.call_soon_threadsafe(asyncio.create_task, _generate())
    
    log.info("Questions generator initialized")
    