"""
Translation service — Multi-provider robust translator.

Primary: Google Translate Android Client (extremely reliable, no 429 ratelimits)
Fallback 1: Google Web Client (gtx)
Fallback 2: MyMemory Translator API
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import urllib.parse
import urllib.request
from typing import Tuple

from config import LANGUAGES

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Headers for providers
# ──────────────────────────────────────────────────────────────────────────────
_ANDROID_USER_AGENT = "AndroidTranslate/5.3.0.RC02.130475354-53000263 5.1 phone TRANSLATE_OPM5_TEST_1"
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ──────────────────────────────────────────────────────────────────────────────
# Simple LRU cache
# ──────────────────────────────────────────────────────────────────────────────
_CACHE: dict[str, tuple[str, str]] = {}
_CACHE_MAX = 3000


def _cache_key(text: str, src: str, tgt: str) -> str:
    return hashlib.md5(f"{src}|{tgt}|{text}".encode()).hexdigest()


def _put_cache(key: str, value: tuple[str, str]) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        for k in list(_CACHE.keys())[:200]:
            _CACHE.pop(k, None)
    _CACHE[key] = value


# ──────────────────────────────────────────────────────────────────────────────
# Translation Engines
# ──────────────────────────────────────────────────────────────────────────────
def _translate_google_android(text: str, src: str, tgt: str) -> tuple[str, str]:
    """Primary engine: Google Translate via Android Client API (no 429 rate limits)."""
    tgt_norm = tgt.replace("zh-cn", "zh-CN").replace("zh-tw", "zh-TW")
    src_norm = "auto" if src == "auto" else src

    params = urllib.parse.urlencode({
        "client": "at",
        "sl": src_norm,
        "tl": tgt_norm,
        "dt": "t",
        "q": text,
    })
    url = f"https://translate.google.com/translate_a/single?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _ANDROID_USER_AGENT})

    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    translated = "".join([s[0] for s in data[0] if s and s[0]])
    detected = data[2] if len(data) > 2 and isinstance(data[2], str) else src_norm
    if not translated:
        raise ValueError("Empty translation from Google Android")
    return translated, detected


def _translate_google_web(text: str, src: str, tgt: str) -> tuple[str, str]:
    """Fallback 1: Google Web client."""
    tgt_norm = tgt.replace("zh-cn", "zh-CN").replace("zh-tw", "zh-TW")
    src_norm = "auto" if src == "auto" else src

    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl": src_norm,
        "tl": tgt_norm,
        "dt": "t",
        "dj": "1",
        "q": text,
    })
    url = f"https://translate.googleapis.com/translate_a/single?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})

    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    translated = "".join(s.get("trans", "") for s in data.get("sentences", []))
    detected = data.get("src", src_norm)
    if not translated:
        raise ValueError("Empty translation from Google Web")
    return translated, detected


def _translate_mymemory(text: str, src: str, tgt: str) -> tuple[str, str]:
    """Fallback 2: MyMemory API."""
    src_code = "uz" if src == "auto" else src
    tgt_code = tgt.split("-")[0]
    src_code = src_code.split("-")[0]

    params = urllib.parse.urlencode({
        "q": text,
        "langpair": f"{src_code}|{tgt_code}"
    })
    url = f"https://api.mymemory.translated.net/get?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_USER_AGENT})

    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    translated = data.get("responseData", {}).get("translatedText")
    if not translated:
        raise ValueError("Empty translation from MyMemory")
    return translated, src_code


def _do_translate_resilient(text: str, src: str, tgt: str) -> tuple[str, str]:
    """Try engines in priority order with graceful fallback."""
    engines = [
        ("Google Android", _translate_google_android),
        ("Google Web", _translate_google_web),
        ("MyMemory", _translate_mymemory),
    ]

    last_err = None
    for name, engine in engines:
        try:
            return engine(text, src, tgt)
        except Exception as exc:
            logger.warning("Engine %s failed: %s", name, exc)
            last_err = exc

    raise RuntimeError(f"All translation engines failed: {last_err}")


# ──────────────────────────────────────────────────────────────────────────────
# Public async API
# ──────────────────────────────────────────────────────────────────────────────
async def translate_text(
    text: str,
    target: str,
    source: str = "auto",
) -> Tuple[str, str]:
    text = text.strip()
    if not text:
        return "", source

    key = _cache_key(text, source, target)
    if key in _CACHE:
        return _CACHE[key]

    loop = asyncio.get_event_loop()
    translated, detected = await loop.run_in_executor(
        None,
        functools.partial(_do_translate_resilient, text=text, src=source, tgt=target),
    )

    result = (translated, detected)
    _put_cache(key, result)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────
def lang_display(code: str) -> str:
    if not code:
        return "UNKNOWN"
    info = LANGUAGES.get(code.lower().replace("-", "_").replace("_", "-"), {})
    if not info:
        info = LANGUAGES.get(code.split("-")[0].lower(), {})
    if not info:
        return code.upper()
    return f"{info['flag']} {info['name']}"


def lang_native(code: str) -> str:
    if not code:
        return ""
    info = LANGUAGES.get(code.lower(), {})
    return info.get("native", code.upper())


def supported_languages() -> list[str]:
    return list(LANGUAGES.keys())
