import asyncio
import logging
from difflib import SequenceMatcher
from functools import wraps
from typing import Callable, Optional

import google.generativeai as genai
from google.api_core import exceptions
from google.rpc.error_details_pb2 import RetryInfo

from .api_key_manager import ApiKeyManager
from .config import GENERATION_CONFIG, SAFETY_SETTINGS


log = logging.getLogger(__name__)


class GenerationError(Exception):
    pass


class GeminiEnglishHelper:

    def __init__(self, api_key_manager: ApiKeyManager, *, model_name: str="gemini-2.0-flash", max_retry_attempts: int=5, retry_delay: int=1):
        self.api_key_manager = api_key_manager
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay # seconds
        
        self.gemini_model = genai.GenerativeModel(model_name, safety_settings=SAFETY_SETTINGS)
        self.retry_attempts = 0

    prepositions = [
        "the", "about", "above", "across", "after", "against", "along", "among",
        "around", "at", "before", "behind", "below", "beneath", "beside",
        "between", "beyond", "but", "by", "concerning", "despite", "down",
        "during", "except", "for", "from", "in", "inside", "into", "like",
        "near", "of", "off", "on", "onto", "out", "outside", "over", "past",
        "regarding", "round", "since", "through", "throughout", "to", "toward",
        "under", "underneath", "until", "up", "upon", "with", "within", "without"
    ]


    def blankify(self, word: str) -> str:
        if word.lower() in self.prepositions:
            return "___"
        if len(word) == 0:
            return ""
        if len(word) == 1:
            return "___"
        if len(word) <= 3:
            return "___"
        if word.endswith("ed"):
            return word[0] + "___"
        if word.endswith("ing"):
            return word[0] + "___"
        if len(word) >= 4:
            return word[0] + "____" + word[-1]
        

    @staticmethod
    def trim_empty_lines(text: str) -> str:
        return "\n".join([line for line in text.splitlines() if line.strip() != ""])
    
    def retry(func: Callable):
        @wraps(func)
        async def wrapper(self: "GeminiEnglishHelper", *args, **kwargs):
            self.retry_attempts += 1
            if self.retry_attempts <= self.max_retry_attempts:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    log.debug(f"Error in {func.__name__}: {e}")
                    self.api_key_manager.wait_for_any_key()
                    await asyncio.sleep(self.retry_delay)
                    return await wrapper(self, *args, **kwargs)
            else:
                log.debug(f"Max retry attempts reached for {func.__name__}")
                return None
        return wrapper
    

    @retry
    async def get_sentence(self, phrase: str) -> str:

        genai.configure(api_key=await self.api_key_manager.get_available_api_key())
        
        try:
            response = await self.gemini_model.generate_content_async(
                f"You are a sentence-making tool. Make *1* short sentence. The sentence must use `{phrase}`."
                f"Do not use other hard words and Markdowns. The sentence should look like a vocabulary test sentence."
                f"After the sentence, give a **whole** sentence **Traditional Chinese** translation. Use `|` to separate English sentence and Chinese translation.",
                generation_config=GENERATION_CONFIG
            )
            return self.trim_empty_lines(response.text)
        
        except exceptions.TooManyRequests as e:
            
            for detail in e.details:
                if isinstance(detail, RetryInfo):
                    retry_delay = detail.retry_delay.seconds
                    await self.api_key_manager.update_retry_delay(retry_delay)
                    
            raise GenerationError(f"Phrase: '{phrase}' - Rate limit exceeded, retrying: {retry_delay} seconds")
        

    @retry
    async def check(self, sentence: str, phrase: str, similarity: float) -> Optional[dict[str, str]]:

        if similarity < 0.5:
            raise GenerationError(f"Sentence: '{sentence}' - Similarity too low: {similarity:.2f}")

        if "|" not in sentence:
            raise GenerationError(f"Sentence: '{sentence}' - No '|' found in response")

        english, chinese = sentence.split("|", 1)
        english = english.strip()
        chinese = chinese.strip()

        if not english.isascii():
            raise GenerationError(f"Sentence: '{sentence}' - English part contains non-ASCII characters: '{english}'")

        elif "_" in chinese:
            raise GenerationError(f"Sentence: '{sentence}' - Chinese part contains underscores: '{chinese}'")   

        return {
            "sentence": sentence,
            "appear": phrase.lower()
        }
            

    async def question(self, phrase: str) -> Optional[dict[str, str]]:
        text: Optional[str] = await self.get_sentence(phrase)
        
        if text is None:
            log.debug(f"Failed to get sentence from API. phrase: '{phrase}'")
            return None
        
        sentence_words = text.split()
        best_phrase, similarity, best_match_positions = self.best_match(text, phrase)

        for i, best_word in zip(best_match_positions, best_phrase.split()):
            if i < len(sentence_words):
                sentence_words[i] = self.blankify(best_word)
            else:
                log.warning("Index %d out of range for sentence: '%s'", i, text)

        sentence_with_blank = " ".join(sentence_words).strip()
        return await self.check(sentence_with_blank, phrase, similarity)
    

    def best_match(self, text: str, target_phrase: str) -> tuple[str, float, list[int]]:
        words = text.split()
        target_words = target_phrase.split()
        target_len = len(target_words)

        best_similarity = 0.0
        best_match = ""
        best_positions = []

        if target_len == 1:
            for i, word in enumerate(words):
                clean_word = word.strip(".,!?;:。，！？；：") 
                sim = self.check_similarity(clean_word, target_phrase)
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = clean_word
                    best_positions = [i]
        else:
            for i in range(len(words) - target_len + 1):
                chunk = " ".join(words[i:i + target_len])
                sim = self.check_similarity(chunk, target_phrase)
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = chunk
                    best_positions = list(range(i, i + target_len))

        return best_match, best_similarity, best_positions


    def check_similarity(self, phrase1: str, phrase2: str) -> float:
        return SequenceMatcher(None, phrase1.lower(), phrase2.lower()).ratio()