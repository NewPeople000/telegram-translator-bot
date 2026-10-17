"""
Vocabulary handlers — list, delete, and inline save.
"""

from __future__ import annotations

import logging
import urllib.parse

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database.db import (
    get_vocab_list,
    count_vocab,
    delete_word,
    save_word,
    get_user,
)
from keyboards.keyboards import vocab_list_kb, main_menu_kb, confirm_delete_kb
from services.translator import lang_display

logger = logging.getLogger(__name__)

PAGE_SIZE = 5

# ──────────────────────────────────────────────────────────────────────────────
# /vocab command + "📚 Lug'atim" button
# ──────────────────────────────────────────────────────────────────────────────
async def vocab_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await _show_vocab_page(update, context, user_id, page=0, edit=False)


async def _show_vocab_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    page: int,
    edit: bool,
) -> None:
    total = await count_vocab(user_id)
    words = await get_vocab_list(user_id, limit=PAGE_SIZE, offset=page * PAGE_SIZE)

    if not words:
        text = (
            "📚 *Lug'atim*\n\n"
            "Hali hech qanday so'z saqlanmagan.\n"
            "Tarjimadan so'ng *💾 Lug'atga saqlash* tugmasini bosing."
        )
        kb = main_menu_kb()
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return

    lines = ["📚 *Lug'atim*\n", f"📌 Jami so'zlar: *{total}*\n"]
    for w in words:
        src_fl = lang_display(w["src_lang"])
        tgt_fl = lang_display(w["tgt_lang"])
        lines.append(
            f"\n`#{w['id']}` {src_fl}→{tgt_fl}\n"
            f"   📖 *{w['original']}*\n"
            f"   ✅ _{w['translation']}_\n"
            f"   🔄 Ko'rib chiqilgan: {w['review_count']}x"
        )

    text = "\n".join(lines)
    kb = vocab_list_kb(list(words), page=page, total=total, page_size=PAGE_SIZE)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: vocab pagination
# ──────────────────────────────────────────────────────────────────────────────
async def vocab_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, page_str = query.data.split(":")
    page = int(page_str)
    await _show_vocab_page(update, context, query.from_user.id, page=page, edit=True)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: delete word (confirm → execute)
# ──────────────────────────────────────────────────────────────────────────────
async def del_word_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, vocab_id_str = query.data.split(":")
    vocab_id = int(vocab_id_str)

    await query.edit_message_text(
        f"⚠️ #{vocab_id} raqamli so'zni o'chirishni tasdiqlaysizmi?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=confirm_delete_kb(vocab_id),
    )


async def confirm_del_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, vocab_id_str = query.data.split(":")
    vocab_id = int(vocab_id_str)
    user_id = query.from_user.id

    deleted = await delete_word(user_id, vocab_id)
    if deleted:
        await query.answer("🗑 So'z o'chirildi!", show_alert=False)
    else:
        await query.answer("❌ So'z topilmadi.", show_alert=True)

    await _show_vocab_page(update, context, user_id, page=0, edit=True)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: save word from translation
# ──────────────────────────────────────────────────────────────────────────────
async def save_word_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Format: save_word:src:tgt:encoded_orig:encoded_tran
    parts = query.data.split(":")
    # parts[0] = "save_word", [1]=src, [2]=tgt, [3]=enc_orig, [4]=enc_tran
    if len(parts) < 5:
        await query.answer("❌ Ma'lumot xato!", show_alert=True)
        return

    src = parts[1]
    tgt = parts[2]
    original = urllib.parse.unquote(parts[3])
    translation = urllib.parse.unquote(parts[4])
    user_id = query.from_user.id

    saved = await save_word(user_id, original, translation, src, tgt)
    if saved:
        await query.answer("✅ So'z lug'atga saqlandi!", show_alert=True)
    else:
        await query.answer("ℹ️ Bu so'z allaqachon lug'atda bor.", show_alert=True)
