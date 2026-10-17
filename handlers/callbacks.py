"""
Central callback router — dispatches all InlineKeyboardButton callbacks.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.vocabulary import (
    vocab_page_callback,
    del_word_callback,
    confirm_del_callback,
    save_word_callback,
)
from handlers.quiz import quiz_answer_callback, quiz_skip_callback
from handlers.settings import (
    set_source_callback,
    set_target_callback,
    src_lang_selected,
    tgt_lang_selected,
)
from handlers.vocabulary import _show_vocab_page
from keyboards.keyboards import main_menu_kb

logger = logging.getLogger(__name__)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data: str = query.data or ""

    # ── Vocabulary ────────────────────────────────────────────────────────────
    if data.startswith("vocab_page:"):
        await vocab_page_callback(update, context)

    elif data.startswith("del_word:"):
        await del_word_callback(update, context)

    elif data.startswith("confirm_del:"):
        await confirm_del_callback(update, context)

    elif data.startswith("save_word:"):
        await save_word_callback(update, context)

    # ── Quiz ──────────────────────────────────────────────────────────────────
    elif data.startswith("quiz_ans:"):
        await quiz_answer_callback(update, context)

    elif data.startswith("quiz_skip:"):
        await quiz_skip_callback(update, context)

    # ── Settings ──────────────────────────────────────────────────────────────
    elif data == "set_source":
        await set_source_callback(update, context)

    elif data == "set_target":
        await set_target_callback(update, context)

    elif data.startswith("src_lang:"):
        await src_lang_selected(update, context)

    elif data.startswith("tgt_lang:"):
        await tgt_lang_selected(update, context)

    # ── Navigation ────────────────────────────────────────────────────────────
    elif data == "back:main":
        await query.answer()
        await query.edit_message_text(
            "🏠 Bosh menyuga qaytdingiz.",
            reply_markup=None,
        )

    elif data == "back:vocab":
        await query.answer()
        await _show_vocab_page(update, context, query.from_user.id, page=0, edit=True)

    elif data == "change_target":
        await query.answer()
        await set_target_callback(update, context)

    elif data == "retranslate":
        await query.answer("🔄 Qayta tarjima qilish uchun matnni yuboring.")

    else:
        await query.answer()
        logger.warning("Unknown callback: %s", data)
