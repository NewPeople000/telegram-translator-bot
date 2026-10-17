"""
Translation message handler — processes any plain text the user sends.
"""

from __future__ import annotations

import logging
import urllib.parse

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from database.db import get_user, upsert_user
from keyboards.keyboards import translation_actions_kb, main_menu_kb
from services.translator import translate_text, lang_display, lang_native
from config import LANGUAGES

logger = logging.getLogger(__name__)

# Emoji strip helpers (keep only first 400 chars for translation)
_MAX_LEN = 2000

# ──────────────────────────────────────────────────────────────────────────────
# Main translate handler
# ──────────────────────────────────────────────────────────────────────────────
async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (update.message.text or "").strip()

    # Skip menu button texts
    MENU_BUTTONS = {
        "🌐 Tarjima qilish", "📚 Lug'atim", "🎯 Quiz / Test",
        "⚙️ Sozlamalar", "📊 Statistika", "❓ Yordam",
    }
    if text in MENU_BUTTONS:
        return  # Let other handlers catch these

    if not text:
        return

    if len(text) > _MAX_LEN:
        await update.message.reply_text(
            f"⚠️ Matn juda uzun! Maksimal {_MAX_LEN} ta belgi.",
            reply_markup=main_menu_kb(),
        )
        return

    # Fetch user preferences
    await upsert_user(user.id, user.username, user.full_name)
    db_user = await get_user(user.id)
    src_lang = db_user["source_lang"] if db_user else "auto"
    tgt_lang = db_user["target_lang"] if db_user else "en"

    # Show typing indicator
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        translated, detected_src = await translate_text(text, target=tgt_lang, source=src_lang)
    except ValueError as exc:
        await update.message.reply_text(f"❌ Xato: {exc}", reply_markup=main_menu_kb())
        return
    except RuntimeError as exc:
        await update.message.reply_text(
            "❌ Tarjima xizmatida xato yuz berdi. Iltimos keyinroq urinib ko'ring.",
            reply_markup=main_menu_kb(),
        )
        logger.error("Translation runtime error: %s", exc)
        return

    # Compose the result message
    src_display = lang_display(detected_src) if detected_src != "auto" else "🔍 Auto"
    tgt_display = lang_display(tgt_lang)

    result = (
        f"📝 *Asl matn* [{src_display}]:\n"
        f"`{text[:300]}`\n\n"
        f"✅ *Tarjima* [{tgt_display}]:\n"
        f"{translated}"
    )

    # Build action keyboard (encode to URL-safe for callback_data)
    enc_orig = urllib.parse.quote(text[:60], safe="")
    enc_tran = urllib.parse.quote(translated[:60], safe="")
    kb = translation_actions_kb(
        original=text[:60],
        translation=translated[:60],
        src=detected_src if detected_src != "auto" else "en",
        tgt=tgt_lang,
    )

    await update.message.reply_text(result, parse_mode="Markdown", reply_markup=kb)

    # Store last translation in context for retranslate
    context.user_data["last_translation"] = {
        "original": text,
        "translation": translated,
        "src": detected_src,
        "tgt": tgt_lang,
    }
