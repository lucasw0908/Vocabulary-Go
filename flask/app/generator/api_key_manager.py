import asyncio
import logging
import time
import threading
from collections import deque
from typing import Callable

from ..config import API_MODEL_TYPE


log = logging.getLogger(__name__)


class ApiKeyManager:
    
    def __init__(self, api_keys: list[str]):
        self.api_keys = deque(self.key_filter(api_keys))
        self.available = {key: True for key in api_keys}
        

    def key_filter(self, api_keys: list[str]) -> list[str]:
        if API_MODEL_TYPE == "gemini":
            return [key for key in api_keys if key.startswith("AIzaSy")]
        
        if API_MODEL_TYPE == "groq":
            return [key for key in api_keys if key.startswith("gsk_")]
            

    async def get_available_api_key(self) -> str:
        for _ in range(len(self.api_keys)):
            key = self.api_keys[0]
            
            if self.available[key]:
                self.api_keys.rotate(1)
                return key
            
        log.debug("No available API keys found. Retrying...")
        
        while not any(self.available.values()):
            await asyncio.sleep(3)
        
        return await self.get_available_api_key()
    
    
    def wait_for_any_key(self):
        while not any(self.available.values()):
            time.sleep(3)
    
    
    @staticmethod
    def _cooldown_thread(key: str, retry_delay: int, available: Callable):
        time.sleep(retry_delay)
        is_kay_available: dict[str, bool] = available()
        if not is_kay_available[key]:
            is_kay_available.update({key: True})
    
    
    async def update_retry_delay(self, retry_delay):
        key = self.api_keys[0]
        self.available[key] = False
        thread = threading.Thread(target=self._cooldown_thread, args=(key, retry_delay, lambda: self.available), daemon=True)
        thread.start()