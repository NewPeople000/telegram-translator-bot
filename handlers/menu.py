"""
Menu button text router — dispatches Reply keyboard button presses.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from handlers.start import help_handler
from handlers.vocabulary import vocab_handler
from handlers.quiz import quiz_handler
from handlers.settings import settings_handler
from handlers.stats import stats_handler


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()

    mapping = {
        "📚 Lug'atim":    vocab_handler,
        "🎯 Quiz / Test": quiz_handler,
        "⚙️ Sozlamalar":  settings_handler,
        "📊 Statistika":  stats_handler,
        "❓ Yordam":      help_handler,
    }

    handler = mapping.get(text)
    if handler:
        await handler(update, context)
