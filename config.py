"""
Configuration module for the Translator Bot.
All sensitive data is loaded from environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Dict

# ---------------------------------------------------------------------------
# Bot token — set via environment variable or replace the default for testing
# ---------------------------------------------------------------------------
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "translator_bot.db")

# ---------------------------------------------------------------------------
# Language catalogue  (20+ languages with flags & native names)
# ---------------------------------------------------------------------------
LANGUAGES: Dict[str, Dict[str, str]] = {
    "en":    {"name": "English",    "flag": "🇬🇧", "native": "English"},
    "ru":    {"name": "Russian",    "flag": "🇷🇺", "native": "Русский"},
    "uz":    {"name": "Uzbek",      "flag": "🇺🇿", "native": "O'zbek"},
    "de":    {"name": "German",     "flag": "🇩🇪", "native": "Deutsch"},
    "fr":    {"name": "French",     "flag": "🇫🇷", "native": "Français"},
    "es":    {"name": "Spanish",    "flag": "🇪🇸", "native": "Español"},
    "it":    {"name": "Italian",    "flag": "🇮🇹", "native": "Italiano"},
    "tr":    {"name": "Turkish",    "flag": "🇹🇷", "native": "Türkçe"},
    "ar":    {"name": "Arabic",     "flag": "🇸🇦", "native": "العربية"},
    "zh-cn": {"name": "Chinese",    "flag": "🇨🇳", "native": "中文"},
    "ja":    {"name": "Japanese",   "flag": "🇯🇵", "native": "日本語"},
    "ko":    {"name": "Korean",     "flag": "🇰🇷", "native": "한국어"},
    "pt":    {"name": "Portuguese", "flag": "🇵🇹", "native": "Português"},
    "hi":    {"name": "Hindi",      "flag": "🇮🇳", "native": "हिन्दी"},
    "fa":    {"name": "Persian",    "flag": "🇮🇷", "native": "فارسی"},
    "pl":    {"name": "Polish",     "flag": "🇵🇱", "native": "Polski"},
    "uk":    {"name": "Ukrainian",  "flag": "🇺🇦", "native": "Українська"},
    "kk":    {"name": "Kazakh",     "flag": "🇰🇿", "native": "Қазақша"},
    "nl":    {"name": "Dutch",      "flag": "🇳🇱", "native": "Nederlands"},
    "sv":    {"name": "Swedish",    "flag": "🇸🇪", "native": "Svenska"},
    "no":    {"name": "Norwegian",  "flag": "🇳🇴", "native": "Norsk"},
    "fi":    {"name": "Finnish",    "flag": "🇫🇮", "native": "Suomi"},
    "he":    {"name": "Hebrew",     "flag": "🇮🇱", "native": "עברית"},
    "id":    {"name": "Indonesian", "flag": "🇮🇩", "native": "Bahasa Indonesia"},
    "vi":    {"name": "Vietnamese", "flag": "🇻🇳", "native": "Tiếng Việt"},
}

# Language codes list for quick lookup
LANGUAGE_CODES = list(LANGUAGES.keys())

# ---------------------------------------------------------------------------
# Default user preferences
# ---------------------------------------------------------------------------
DEFAULT_SOURCE_LANG: str = "auto"   # auto-detect
DEFAULT_TARGET_LANG: str = "en"

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------
MAX_VOCAB_PER_USER: int = 500        # max saved words per user
QUIZ_BATCH_SIZE: int = 5             # words per quiz session

# ---------------------------------------------------------------------------
# Inline keyboard layout
# ---------------------------------------------------------------------------
LANG_KEYBOARD_COLUMNS: int = 3      # columns in language picker

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str  = os.getenv("LOG_FILE",  "bot.log")
