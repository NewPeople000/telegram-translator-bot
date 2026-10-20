"""
Quiz (flashcard) handler — language selection & multiple-choice quiz system.
"""

from __future__ import annotations

import logging
import random
from typing import List, Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database.db import get_quiz_words, record_quiz_result, count_vocab
from keyboards.keyboards import (
    quiz_languages_kb,
    quiz_options_kb,
    quiz_finished_kb,
    main_menu_kb,
)
from data.quiz_words import generate_quiz_session, QUIZ_LANGUAGES
from config import QUIZ_BATCH_SIZE

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# /quiz command  +  "🎯 Quiz / Test" button
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available languages for the quiz."""
    user_id = update.effective_user.id
    vocab_count = await count_vocab(user_id)
    has_user_vocab = vocab_count >= 2

    text = (
        "🎯 *Quiz / Test bo'limi*\n\n"
        "Qaysi tildagi so'zlar bo'yicha test topshirmoqchisiz?\n"
        "Quyidagi tillardan birini tanlang:"
    )

    kb = quiz_languages_kb(has_user_vocab=has_user_vocab)
    msg = update.effective_message
    await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: Return to language picker
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_choose_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to language selection menu."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    vocab_count = await count_vocab(user_id)
    has_user_vocab = vocab_count >= 2

    text = (
        "🎯 *Quiz / Test bo'limi*\n\n"
        "Qaysi tildagi so'zlar bo'yicha test topshirmoqchisiz?\n"
        "Quyidagi tillardan birini tanlang:"
    )
    kb = quiz_languages_kb(has_user_vocab=has_user_vocab)

    try:
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception:
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: Start quiz for chosen language
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection or retry, prepare question queue, and send 1st question."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if data.startswith("quiz_retry:"):
        lang_code = data.split(":")[1]
    else:
        lang_code = data.split(":")[1]

    user_id = update.effective_user.id

    if lang_code == "my_vocab":
        words = await get_quiz_words(user_id, batch=QUIZ_BATCH_SIZE)
        if len(words) < 2:
            await query.answer("Lug'atingizda kamida 2 ta so'z bo'lishi kerak!", show_alert=True)
            return

        # Build questions from user's vocabulary
        raw_words = [dict(w) for w in words]
        all_translations = [w["translation"] for w in raw_words]
        fallback_trans = ["suv", "kitob", "do'st", "uy", "vaqt", "ish", "shahar", "yurak"]

        questions = []
        for word in raw_words:
            correct = word["translation"]
            distractors = [t for t in all_translations if t != correct]
            while len(distractors) < 3:
                fb = random.choice(fallback_trans)
                if fb != correct and fb not in distractors:
                    distractors.append(fb)
            distractors = random.sample(distractors, 3)
            options = distractors + [correct]
            random.shuffle(options)
            questions.append({
                "word": word["original"],
                "correct": correct,
                "options": options,
                "correct_idx": options.index(correct),
                "lang": "my_vocab",
                "lang_name": "📚 Shaxsiy lug'at",
                "vocab_id": word["id"],
            })
    else:
        questions = generate_quiz_session(lang_code, count=QUIZ_BATCH_SIZE)
        if not questions:
            await query.answer("Bu til uchun so'zlar topilmadi!", show_alert=True)
            return

    context.user_data["quiz_queue"] = questions
    context.user_data["quiz_score"] = {"correct": 0, "total": 0}
    context.user_data["quiz_lang"] = lang_code
    context.user_data["quiz_initial_total"] = len(questions)

    await _send_quiz_question(update, context, is_new=False)


# ──────────────────────────────────────────────────────────────────────────────
# Internal: send or edit question
# ──────────────────────────────────────────────────────────────────────────────
async def _send_quiz_question(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new: bool = False
) -> None:
    queue: List[dict] = context.user_data.get("quiz_queue", [])
    score: dict = context.user_data.get("quiz_score", {"correct": 0, "total": 0})
    initial_total: int = context.user_data.get("quiz_initial_total", 5)

    if not queue:
        await _finish_quiz(update, context)
        return

    q = queue[0]
    context.user_data["quiz_correct_idx"] = q["correct_idx"]

    q_num = initial_total - len(queue) + 1

    text = (
        f"🎯 *Savol {q_num}/{initial_total}*  ({q['lang_name']})\n\n"
        f"📖 So'z: *{q['word']}*\n\n"
        f"❓ O'zbekcha to'g'ri tarjimasini tanlang:"
    )

    kb = quiz_options_kb(q["options"])

    msg = update.effective_message
    if is_new:
        await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        try:
            await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        except Exception:
            await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: quiz answer selected
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    try:
        chosen_idx = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        await query.answer()
        return

    queue: List[dict] = context.user_data.get("quiz_queue", [])
    score: dict = context.user_data.get("quiz_score", {"correct": 0, "total": 0})

    if not queue:
        await query.answer("Quiz tugagan!", show_alert=False)
        return

    q = queue[0]
    is_correct = chosen_idx == q["correct_idx"]

    score["total"] += 1
    if is_correct:
        score["correct"] += 1
    context.user_data["quiz_score"] = score

    # Record in DB (updates user stats)
    user_id = query.from_user.id
    await record_quiz_result(user_id, is_correct, vocab_id=q.get("vocab_id"))

    # Remove answered question from queue
    context.user_data["quiz_queue"] = queue[1:]

    if is_correct:
        await query.answer("✅ To'g'ri!", show_alert=False)
    else:
        await query.answer(f"❌ Noto'g'ri! To'g'ri javob: {q['correct']}", show_alert=True)

    await _send_quiz_question(update, context, is_new=False)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: skip question
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("⏭ O'tkazib yuborildi")

    queue: List[dict] = context.user_data.get("quiz_queue", [])
    score: dict = context.user_data.get("quiz_score", {"correct": 0, "total": 0})

    if queue:
        score["total"] += 1
        context.user_data["quiz_score"] = score
        context.user_data["quiz_queue"] = queue[1:]

    await _send_quiz_question(update, context, is_new=False)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: stop quiz early
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("🛑 Test to'xtatildi")
    context.user_data["quiz_queue"] = []
    await _finish_quiz(update, context)


# ──────────────────────────────────────────────────────────────────────────────
# Internal: finish quiz and show summary
# ──────────────────────────────────────────────────────────────────────────────
async def _finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    score: dict = context.user_data.get("quiz_score", {"correct": 0, "total": 0})
    lang_code: str = context.user_data.get("quiz_lang", "en")

    lang_info = QUIZ_LANGUAGES.get(lang_code, {"name": "Test", "flag": "🌐"})
    lang_name = "📚 Shaxsiy lug'at" if lang_code == "my_vocab" else f"{lang_info['flag']} {lang_info['name']}"

    c = score["correct"]
    t = score["total"]
    pct = round((c / t) * 100) if t else 0
    stars = "⭐" * max(1, min(5, round(pct / 20)))

    if pct >= 80:
        praise = "🎉 Ajoyib natija! So'zlarni juda yaxshi bilasiz!"
    elif pct >= 50:
        praise = "💪 Yaxshi natija! Yana biroz mashq qilsangiz, mukammal bo'ladi."
    else:
        praise = "📖 Ko'proq mashq qiling, harakatdan to'xtamang!"

    text = (
        f"🏁 *Quiz yakunlandi!* ({lang_name})\n\n"
        f"✅ To'g'ri javoblar: *{c}/{t}*\n"
        f"📊 Aniqlik: *{pct}%* {stars}\n\n"
        f"{praise}"
    )

    kb = quiz_finished_kb(lang_code)
    msg = update.effective_message

    try:
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception:
        await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
