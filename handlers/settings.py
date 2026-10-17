"""
Settings handler — change source/target language.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database.db import get_user, update_languages, upsert_user
from keyboards.keyboards import settings_kb, language_picker_kb, main_menu_kb
from services.translator import lang_display

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# /settings  +  "⚙️ Sozlamalar" button
# ──────────────────────────────────────────────────────────────────────────────
async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.full_name)
    db_user = await get_user(user.id)

    src = db_user["source_lang"] if db_user else "auto"
    tgt = db_user["target_lang"] if db_user else "en"

    text = (
        "⚙️ *Sozlamalar*\n\n"
        f"📥 Manba tili:  {lang_display(src) if src != 'auto' else '🔍 Avtomatik'}\n"
        f"📤 Maqsad tili: {lang_display(tgt)}\n\n"
        "O'zgartirish uchun quyidagi tugmalardan birini bosing:"
    )
    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=settings_kb(src, tgt),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Callbacks: open language pickers
# ──────────────────────────────────────────────────────────────────────────────
async def set_source_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db_user = await get_user(query.from_user.id)
    current = db_user["source_lang"] if db_user else "auto"

    await query.edit_message_text(
        "📥 *Manba tilini tanlang:*\n_(avto-aniqlash uchun /auto yuboring)_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=language_picker_kb("src_lang", selected=current),
    )


async def set_target_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db_user = await get_user(query.from_user.id)
    current = db_user["target_lang"] if db_user else "en"

    await query.edit_message_text(
        "📤 *Maqsad tilini tanlang:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=language_picker_kb("tgt_lang", selected=current),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Callbacks: language selected
# ──────────────────────────────────────────────────────────────────────────────
async def src_lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, code = query.data.split(":")
    db_user = await get_user(query.from_user.id)
    tgt = db_user["target_lang"] if db_user else "en"

    await update_languages(query.from_user.id, source=code, target=tgt)
    await query.answer(f"✅ Manba til o'rnatildi: {lang_display(code)}")
    await query.edit_message_text(
        f"⚙️ *Sozlamalar yangilandi!*\n\n"
        f"📥 Manba: {lang_display(code)}\n"
        f"📤 Maqsad: {lang_display(tgt)}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=settings_kb(code, tgt),
    )


async def tgt_lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    _, code = query.data.split(":")
    db_user = await get_user(query.from_user.id)
    src = db_user["source_lang"] if db_user else "auto"

    await update_languages(query.from_user.id, source=src, target=code)
    await query.answer(f"✅ Maqsad til o'rnatildi: {lang_display(code)}")
    await query.edit_message_text(
        f"⚙️ *Sozlamalar yangilandi!*\n\n"
        f"📥 Manba: {lang_display(src) if src != 'auto' else '🔍 Avtomatik'}\n"
        f"📤 Maqsad: {lang_display(code)}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=settings_kb(src, code),
    )
