"""
Statistics handler — show user's learning progress.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database.db import get_user_stats, get_user
from keyboards.keyboards import main_menu_kb
from services.translator import lang_display

logger = logging.getLogger(__name__)


def _progress_bar(pct: int, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct}%"


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    stats = await get_user_stats(user_id)
    db_user = await get_user(user_id)

    tgt = db_user["target_lang"] if db_user else "en"
    src = db_user["source_lang"] if db_user else "auto"

    accuracy = stats["accuracy"]
    pbar = _progress_bar(accuracy)

    emoji_level = (
        "🏆 Expert" if accuracy >= 90
        else "🥇 Yaxshi" if accuracy >= 70
        else "📈 O'rta" if accuracy >= 50
        else "🌱 Boshlang'ich"
    )

    text = (
        f"📊 *Sizning statistikangiz*\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"🗣 Joriy tillar:\n"
        f"  📥 Manba: {lang_display(src) if src != 'auto' else '🔍 Avtomatik'}\n"
        f"  📤 Maqsad: {lang_display(tgt)}\n\n"
        f"📚 Saqlangan so'zlar: *{stats['total_words']}* ta\n\n"
        f"🎯 Quiz natijalari:\n"
        f"  📝 Jami urinishlar: *{stats['total_quizzes']}*\n"
        f"  ✅ To'g'ri javoblar: *{stats['correct_quizzes']}*\n"
        f"  📈 Aniqlik: {pbar}\n\n"
        f"🎖 Daraja: *{emoji_level}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Har kuni quiz ishlang — so'zlar yaxshi yodlanadi!_"
    )

    await update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_kb(),
    )
