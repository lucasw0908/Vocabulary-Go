import asyncio
import logging
from difflib import SequenceMatcher
from functools import wraps
from typing import Callable, Optional
from opencc import OpenCC

import aiohttp
import json

from .api_key_manager import ApiKeyManager

log = logging.getLogger(__name__)


class GenerationError(Exception):
    pass


class GeminiEnglishHelper:
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key_manager: ApiKeyManager, *, model_name: str = "gemma2-9b-it",
                 max_retry_attempts: int = 5, retry_delay: int = 1):
        self.api_key_manager = api_key_manager
        self.model_name = model_name
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay  # seconds
        self.retry_attempts = 0
        self.cc = OpenCC('s2t')  # 簡體轉繁體

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
            for attempt in range(1, self.max_retry_attempts + 1):
                try:
                    return await func(self, *args, **kwargs)
                except GenerationError as e:
                    if "429" in str(e):
                        log.warning(f"Rate limited (attempt {attempt}), retrying in {self.retry_delay}s...")
                        self.api_key_manager.wait_for_any_key()  # 換 API key
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        raise
                except Exception as e:
                    log.error(f"Error in {func.__name__} attempt {attempt}: {e}", exc_info=True)
                    self.api_key_manager.wait_for_any_key()
                    await asyncio.sleep(self.retry_delay)
            log.error(f"Max retry attempts reached for {func.__name__}")
            return None
        return wrapper


    async def _groq_request(self, user_prompt: str) -> Optional[str]:
        api_key = await self.api_key_manager.get_available_api_key()
        payload = {"model": self.model_name, "messages":[{"role": "user", "content": user_prompt}]}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 429:
                    retry_after = 2.0
                    await asyncio.sleep(retry_after)
                    return await self._groq_request(user_prompt)
                elif resp.status != 200:
                    error_text = await resp.text()
                    log.error(f"Groq API error: status={resp.status}, body={error_text}")
                    raise GenerationError(f"Groq API error: {resp.status} - {error_text}")

                data = await resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    log.error(f"Unexpected response: {json.dumps(data, ensure_ascii=False)}")
                    raise GenerationError("Unexpected response format")

    @retry
    async def get_sentence(self, phrase: str) -> str:
        prompt = (
            f"You are a sentence-making tool. Make *1* short sentence. The sentence must use `{phrase}`. "
            f"Do not use other hard words and do not use Markdown. The sentence should look like a vocabulary test sentence. "
            f"After the sentence, give a **whole** sentence **Traditional Chinese** translation. "
            f"You MUST use Traditional Chinese characters for the translation, not Simplified Chinese. "
            f"Use `|` to separate the English sentence and the Chinese translation."
        )
        response = await self._groq_request(prompt)
        return self.trim_empty_lines(response)

    @retry
    async def check(self, sentence: str, phrase: str, similarity: float) -> Optional[dict[str, str]]:
        if similarity < 0.5:
            log.warning(f"Low similarity ({similarity:.2f}) for phrase '{phrase}' with sentence '{sentence}'")
            raise GenerationError(f"Sentence: '{sentence}' - Similarity too low: {similarity:.2f}")

        if "|" not in sentence:
            log.error(f"Invalid response: missing '|' separator in '{sentence}'")
            raise GenerationError(f"Sentence: '{sentence}' - No '|' found in response")

        english, chinese = sentence.split("|", 1)
        english = english.strip()
        chinese = chinese.strip()

        # 自動轉繁體
        chinese = self.cc.convert(chinese)

        if not english.isascii():
            log.error(f"English part contains non-ASCII characters: '{english}'")
            raise GenerationError(f"Sentence: '{sentence}' - English part contains non-ASCII characters: '{english}'")

        elif "_" in chinese:
            log.error(f"Chinese translation contains underscores: '{chinese}'")
            raise GenerationError(f"Sentence: '{sentence}' - Chinese part contains underscores: '{chinese}'")

        return {
            "sentence": f"{english}|{chinese}",
            "appear": phrase.lower()
        }

    async def question(self, phrase: str) -> Optional[dict[str, str]]:
        try:
            text: Optional[str] = await self.get_sentence(phrase)

            if text is None:
                log.error(f"Failed to get sentence from API for phrase: '{phrase}'")
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
        except Exception as e:
            log.error(f"Error generating question for phrase '{phrase}': {e}", exc_info=True)
            return None

    def best_match(self, text: str, target_phrase: str) -> tuple[str, float, list[int]]:
        words = text.split()
        target_words = target_phrase.split()
        target_len = len(target_words)

        best_similarity = 0.0
        best_match = ""
        best_positions = []

        try:
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
        except Exception as e:
            log.error(f"Error during best_match calculation: {e}", exc_info=True)

        return best_match, best_similarity, best_positions

    def check_similarity(self, phrase1: str, phrase2: str) -> float:
        try:
            return SequenceMatcher(None, phrase1.lower(), phrase2.lower()).ratio()
        except Exception as e:
            log.error(f"Error calculating similarity between '{phrase1}' and '{phrase2}': {e}", exc_info=True)
            return 0.0
