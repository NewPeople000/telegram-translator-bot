"""
/start  and  /help  command handlers.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from database.db import upsert_user, get_user
from keyboards.keyboards import main_menu_kb
from services.translator import lang_display

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
WELCOME_TEXT = """
🌍 *TranslateBot Pro* ga xush kelibsiz!

Men sizga **25+ tilda** tarjima qilishga va so'zlarni yodlashga yordam beraman.

━━━━━━━━━━━━━━━━━━━━━━━
🌐 *Tarjima* — matn yuboring, darhol tarjima olasiz
📚 *Lug'at* — so'zlarni saqlang va qayta ko'ring
🎯 *Quiz* — turli tillardagi so'zlar bo'yicha test topshiring
⚙️ *Sozlamalar* — manba/maqsad tilni o'zgartiring
📊 *Statistika* — o'z natijalaringizni kuzating
━━━━━━━━━━━━━━━━━━━━━━━

Boshlash uchun matn yozing yoki quyidagi tugmalardan birini bosing 👇
"""

HELP_TEXT = """
❓ *Yordam / Qo'llanma*

*Tarjima qilish:*
Istalgan matnni to'g'ridan-to'g'ri yuboring — bot avtomatik aniqlaydi va tarjima qiladi.

*Lug'at:*
Tarjimadan so'ng "💾 Lug'atga saqlash" tugmasini bosing.

*Quiz:*
Turli tillar (Ingliz, Rus, Turk, Nemis va h.k.) yoki shaxsiy lug'atingiz bo'yicha test topshiring. Har bir to'g'ri javob statistikangizga qo'shiladi.

*Sozlamalar:*
Manba va maqsad tilni o'zgartiring. "auto" — tilni avtomatik aniqlaydi.

*Buyruqlar:*
/start   — Bosh menyu
/help    — Yordam
/stats   — Statistika
/vocab   — Lug'atim
/quiz    — Tez quiz boshlash
/settings — Sozlamalar

📬 Muammo bo'lsa: @YourSupportUsername
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.full_name)

    db_user = await get_user(user.id)
    tgt = db_user["target_lang"] if db_user else "en"

    text = (
        f"👋 Qaytib keldingiz, *{user.first_name}*!\n\n"
        f"Joriy tarjima tili: {lang_display(tgt)}"
        if db_user and db_user["last_active"] != db_user["created_at"]
        else WELCOME_TEXT
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )
