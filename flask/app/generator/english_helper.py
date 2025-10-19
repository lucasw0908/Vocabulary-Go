import asyncio
import logging
import json
from difflib import SequenceMatcher
from functools import wraps
from typing import Callable, Optional, overload
from opencc import OpenCC

import aiohttp
import google.generativeai as genai
from google.api_core import exceptions
from google.rpc.error_details_pb2 import RetryInfo

from .api_key_manager import ApiKeyManager

log = logging.getLogger(__name__)


class APIError(Exception):
    pass

class GenerationError(Exception):
    pass

class RateLimitError(GenerationError):
    pass

class EnglishHelper:

    def __init__(self, api_key_manager: ApiKeyManager, *, model_name: str,
                 max_retry_attempts: int = 5, retry_delay: int = 1):
        self.api_key_manager = api_key_manager
        self.model_name = model_name
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay  # Seconds
        self.retry_attempts = 0
        self.cc = OpenCC("s2t")  # Simplified to Traditional Chinese


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
        async def wrapper(self: "EnglishHelper", *args, **kwargs):
            for attempt in range(1, self.max_retry_attempts + 1):
                try:
                    return await func(self, *args, **kwargs)
                
                except RateLimitError:
                    log.debug(f"Rate limited (attempt {attempt}), retrying in {self.retry_delay}s...")
                    self.api_key_manager.wait_for_any_key()
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                except GenerationError as e:
                    log.debug(f"Generation error in {func.__name__} attempt {attempt}: {e}", exc_info=True)
                    self.api_key_manager.wait_for_any_key()
                    await asyncio.sleep(self.retry_delay)
                    
            log.debug(f"Max retry attempts reached for {func.__name__}")
            return None
        return wrapper
    
    
    @overload
    async def request_api(self, prompt: str) -> str: ...
                

    async def get_sentence(self, phrase: str) -> str:
        prompt = (
            f"You are a sentence-making tool. Make *1* short sentence. The sentence must use `{phrase}`. "
            f"Do not use other hard words and do not use Markdown. The sentence should look like a vocabulary test sentence. "
            f"After the sentence, give a **whole** sentence **Traditional Chinese** translation. "
            f"You MUST use Traditional Chinese characters for the translation, not Simplified Chinese. "
            f"Use `|` to separate the English sentence and the Chinese translation."
        )
        response = await self.request_api(prompt)
        return self.trim_empty_lines(response)
    

    async def check(self, sentence: str, phrase: str, similarity: float) -> Optional[dict[str, str]]:
        if similarity < 0.5:
            raise GenerationError(f"Sentence: '{sentence}' - Similarity too low: {similarity:.2f}")

        if "|" not in sentence:
            raise GenerationError(f"Sentence: '{sentence}' - No '|' found in response")

        english, chinese = sentence.split("|", 1)
        english = english.strip()
        chinese = chinese.strip()

        chinese = self.cc.convert(chinese)

        if not english.isascii():
            raise GenerationError(f"Sentence: '{sentence}' - English part contains non-ASCII characters: '{english}'")

        elif "_" in chinese:
            raise GenerationError(f"Sentence: '{sentence}' - Chinese part contains underscores: '{chinese}'")

        return {
            "sentence": f"{english}|{chinese}",
            "appear": phrase.lower()
        }
        

    @retry
    async def question(self, phrase: str) -> Optional[dict[str, str]]:
        text: Optional[str] = await self.get_sentence(phrase)

        if text is None:
            raise GenerationError(f"Failed to get sentence from API for phrase: '{phrase}'")

        sentence_words = text.split()
        best_phrase, similarity, best_match_positions = self.best_match(text, phrase)

        for i, best_word in zip(best_match_positions, best_phrase.split()):
            if i < len(sentence_words):
                sentence_words[i] = self.blankify(best_word)
            else:
                raise GenerationError(f"Index {i} out of range for sentence: '{text}'")

        sentence_with_blank = " ".join(sentence_words).strip()
        return await self.check(sentence_with_blank, phrase, similarity)
        

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
            raise GenerationError(f"Error during best_match calculation: {e}")

        return best_match, best_similarity, best_positions
    

    def check_similarity(self, phrase1: str, phrase2: str) -> float:
        try:
            return SequenceMatcher(None, phrase1.lower(), phrase2.lower()).ratio()
        except Exception as e:
            log.error(f"Error calculating similarity between '{phrase1}' and '{phrase2}': {e}", exc_info=True)
            return 0.0


class GroqEnglishHelper(EnglishHelper):
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    async def request_api(self, prompt) -> str:
        
        api_key = await self.api_key_manager.get_available_api_key()
        payload = {"model": self.model_name, "messages":[{"role": "user", "content": prompt}]}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                elif resp.status == 401:
                    log.error("Unauthorized: Invalid API key")
                    raise APIError("Unauthorized: Invalid API key")
                
                elif resp.status != 200:
                    error_text = await resp.text()
                    log.error(f"Groq API error: status={resp.status}, body={error_text}")
                    raise GenerationError(f"Groq API error: {resp.status} - {error_text}")

                data = await resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    log.debug(f"Unexpected response: {json.dumps(data, ensure_ascii=False)}")
                    raise GenerationError("Unexpected response format")
                
                
class GeminiEnglishHelper(EnglishHelper):
    GENERATION_CONFIG = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "block_none"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "block_none"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "block_none"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "block_none"
        },
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gemini_model = genai.GenerativeModel(self.model_name, safety_settings=self.SAFETY_SETTINGS)
    
    async def request_api(self, prompt) -> str:
        genai.configure(api_key=await self.api_key_manager.get_available_api_key())
        
        try:
            response = await self.gemini_model.generate_content_async(
                prompt,
                generation_config=self.GENERATION_CONFIG
            )
        
        except exceptions.TooManyRequests as e:
            for detail in e.details:
                if isinstance(detail, RetryInfo):
                    retry_delay = detail.retry_delay.seconds
                    await self.api_key_manager.update_retry_delay(retry_delay)
                    
            raise RateLimitError("Rate limit exceeded")
        
        except exceptions.GoogleAPICallError as e:
            log.error(f"Gemini API call error: {e}", exc_info=True)
            raise APIError(f"Gemini API call error: {e}")
        
        return self.trim_empty_lines(response.text)
    
    

class MistralEnglishHelper(EnglishHelper):
    API_URL = "https://api.mistral.ai/v1/chat/completions"

    async def request_api(self, prompt) -> str:
        api_key = await self.api_key_manager.get_available_api_key()
        payload = {
            "model": self.model_name or "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.API_URL, headers=headers, json=payload) as resp:
                if resp.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif resp.status == 401:
                    log.error("Unauthorized: Invalid API key")
                    raise APIError("Unauthorized: Invalid API key")
                elif resp.status != 200:
                    error_text = await resp.text()
                    log.error(f"Mistral API error: status={resp.status}, body={error_text}")
                    raise GenerationError(f"Mistral API error: {resp.status} - {error_text}")

                data = await resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    log.debug(f"Unexpected response: {json.dumps(data, ensure_ascii=False)}")
                    raise GenerationError("Unexpected response format")