"""
Quiz (flashcard) handler — spaced-repetition style multiple-choice quiz.
"""

from __future__ import annotations

import logging
import random
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database.db import get_quiz_words, record_quiz_result, count_vocab
from keyboards.keyboards import quiz_options_kb, main_menu_kb
from config import QUIZ_BATCH_SIZE

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# /quiz command  +  "🎯 Quiz / Test" button
# ──────────────────────────────────────────────────────────────────────────────
async def quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    total = await count_vocab(user_id)

    if total < 2:
        await update.effective_message.reply_text(
            "📚 *Quiz uchun kamida 2 ta so'z kerak!*\n\n"
            "Tarjima qilib, lug'atga so'z saqlang, keyin qaytib keling. 💪",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_kb(),
        )
        return

    words = await get_quiz_words(user_id, batch=QUIZ_BATCH_SIZE)
    # Shuffle and pick one at a time — store queue in user_data
    context.user_data["quiz_queue"] = [dict(w) for w in words]
    context.user_data["quiz_score"] = {"correct": 0, "total": 0}

    await _send_quiz_question(update, context, is_new=True)


# ──────────────────────────────────────────────────────────────────────────────
# Internal: send next question
# ──────────────────────────────────────────────────────────────────────────────
async def _send_quiz_question(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_new: bool = False
) -> None:
    queue: List[dict] = context.user_data.get("quiz_queue", [])
    score: dict = context.user_data.get("quiz_score", {"correct": 0, "total": 0})

    if not queue:
        # Quiz finished
        c = score["correct"]
        t = score["total"]
        pct = round((c / t) * 100) if t else 0
        stars = "⭐" * min(5, round(pct / 20))

        text = (
            f"🏁 *Quiz yakunlandi!*\n\n"
            f"✅ To'g'ri javoblar: *{c}/{t}*\n"
            f"📊 Natija: *{pct}%* {stars}\n\n"
            + ("🎉 Zo'r natija!" if pct >= 80 else "💪 Davom eting, bo'lasiz!")
        )
        await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_kb())
        return

    word = queue[0]
    vocab_id = word["id"]

    # Build 4 distractor options (use other translations from queue + random)
    correct_answer = word["translation"]
    distractors = [w["translation"] for w in queue[1:] if w["translation"] != correct_answer]

    # Pad distractors if fewer than 3
    FALLBACK = ["house", "run", "beautiful", "water", "time", "hello", "yes", "no", "go", "book"]
    while len(distractors) < 3:
        fb = random.choice(FALLBACK)
        if fb not in distractors and fb != correct_answer:
            distractors.append(fb)

    distractors = random.sample(distractors, min(3, len(distractors)))
    options = distractors + [correct_answer]
    random.shuffle(options)

    correct_idx = options.index(correct_answer)
    context.user_data["quiz_correct_idx"] = correct_idx

    q_num = score["total"] + 1
    total_q = q_num + len(queue) - 1

    text = (
        f"🎯 *Savol {q_num}/{len(queue) + score['total']}*\n\n"
        f"📖 So'z: *{word['original']}*\n\n"
        f"❓ Tarjimasini tanlang:"
    )

    kb = quiz_options_kb(options, vocab_id)

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

    parts = query.data.split(":")
    vocab_id = int(parts[1])
    chosen_idx = int(parts[2])

    correct_idx: int = context.user_data.get("quiz_correct_idx", -1)
    queue: List[dict] = context.user_data.get("quiz_queue", [])
    score: dict = context.user_data.get("quiz_score", {"correct": 0, "total": 0})

    if not queue:
        await query.answer("Quiz tugadi!", show_alert=False)
        return

    word = queue[0]
    is_correct = chosen_idx == correct_idx

    # Update score
    score["total"] += 1
    if is_correct:
        score["correct"] += 1
    context.user_data["quiz_score"] = score

    # Record in DB
    await record_quiz_result(query.from_user.id, vocab_id, is_correct)

    # Pop from queue
    context.user_data["quiz_queue"] = queue[1:]

    feedback = "✅ *To'g'ri!*" if is_correct else f"❌ *Noto'g'ri!*\nTo'g'ri javob: _{word['translation']}_"
    await query.answer(
        "✅ To'g'ri!" if is_correct else f"❌ Noto'g'ri! Javob: {word['translation']}",
        show_alert=not is_correct,
    )

    # Edit current message to show result then send next
    await query.edit_message_text(
        f"{feedback}\n\n⏳ Keyingi savol yuklanmoqda...",
        parse_mode=ParseMode.MARKDOWN,
    )

    context.user_data["_last_quiz_msg"] = query.message
    await _send_quiz_question(update, context, is_new=True)


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
