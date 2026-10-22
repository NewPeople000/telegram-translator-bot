"""
TranslateBot Pro — entry point.

Run:
    BOT_TOKEN=<token> python bot.py
"""

from __future__ import annotations

import asyncio
import io
import logging
import sys

# Fix Windows terminal UTF-8 encoding (emoji support)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Load .env file BEFORE importing config (so os.getenv picks up the token)
from dotenv import load_dotenv
load_dotenv()

from telegram import BotCommand
from telegram.ext import (  
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, LOG_LEVEL, LOG_FILE
from database.db import init_db
from handlers.start import start_handler, help_handler
from handlers.translate import translate_handler
from handlers.vocabulary import vocab_handler
from handlers.quiz import quiz_handler
from handlers.settings import settings_handler
from handlers.stats import stats_handler
from handlers.callbacks import callback_router
from handlers.menu import menu_router

# ──────────────────────────────────────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Bot commands visible in Telegram UI
# ──────────────────────────────────────────────────────────────────────────────
BOT_COMMANDS = [
    BotCommand("start",    "🏠 Bosh menyu"),
    BotCommand("help",     "❓ Yordam"),
    BotCommand("vocab",    "📚 Lug'atim"),
    BotCommand("quiz",     "🎯 Quiz boshlash"),
    BotCommand("stats",    "📊 Statistika"),
    BotCommand("settings", "⚙️ Sozlamalar"),
]



# ──────────────────────────────────────────────────────────────────────────────
# Optional Health Server for cloud platforms (Render, Koyeb, etc.)
# ──────────────────────────────────────────────────────────────────────────────
def _start_health_server() -> None:
    port_env = os.getenv("PORT")
    if not port_env:
        return
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"TranslateBot Pro is healthy and active!")

            def log_message(self, format, *args):
                return

        port = int(port_env)
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info("Health server %d-portda ishga tushirildi.", port)
    except Exception as exc:
        logger.warning("Health serverni ishga tushirishda xatolik: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
async def _setup(app: Application) -> None:
    """post_init hook: DB init + register Telegram commands."""
    await init_db()
    await app.bot.set_my_commands(BOT_COMMANDS)
    logger.info("TranslateBot Pro tayyor!")


def main() -> None:
    _start_health_server()
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "Bot token topilmadi!\n"
            "  .env fayliga BOT_TOKEN=<token> qo'shing."
        )
        sys.exit(1)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_setup)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start",    start_handler))
    app.add_handler(CommandHandler("help",     help_handler))
    app.add_handler(CommandHandler("vocab",    vocab_handler))
    app.add_handler(CommandHandler("quiz",     quiz_handler))
    app.add_handler(CommandHandler("stats",    stats_handler))
    app.add_handler(CommandHandler("settings", settings_handler))

    # Inline button callbacks
    app.add_handler(CallbackQueryHandler(callback_router))

    # Reply keyboard menu buttons
    MENU_PATTERN = (
        "^(📚 Lug'atim|🎯 Quiz / Test|⚙️ Sozlamalar|📊 Statistika|❓ Yordam)$"
    )
    app.add_handler(MessageHandler(filters.Regex(MENU_PATTERN), menu_router))

    # "🌐 Tarjima qilish" button
    app.add_handler(
        MessageHandler(
            filters.Regex("^🌐 Tarjima qilish$"),
            lambda u, c: u.message.reply_text(
                "✍️ Tarjima qilmoqchi bo'lgan matningizni yuboring:"
            ),
        )
    )

    # All other text → translate
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, translate_handler)
    )

    logger.info("TranslateBot Pro ishga tushdi! Ctrl+C bilan to'xtatish mumkin.")
    # Python 3.14 fix: explicitly create and set an event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # PTB manages its own event loop — do NOT wrap in asyncio.run()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
