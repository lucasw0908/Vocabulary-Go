from .english_helper import GroqEnglishHelper, GeminiEnglishHelper, MistralEnglishHelper

API_INFO = {
    "groq": {
        "helper_class": GroqEnglishHelper,
        "prefix": "gsk_"
    },
    "gemini": {
        "helper_class": GeminiEnglishHelper,
        "prefix": "AIzaSy"
    },
    "mistral": {
        "helper_class": MistralEnglishHelper,
        "prefix": None
    }
}