"""
Keyboards — all inline & reply keyboard builders.
"""

from __future__ import annotations

from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from config import LANGUAGES, LANG_KEYBOARD_COLUMNS

# ──────────────────────────────────────────────────────────────────────────────
# Main menu (Reply keyboard)
# ──────────────────────────────────────────────────────────────────────────────
def main_menu_kb() -> ReplyKeyboardMarkup:
    buttons = [
        ["🌐 Tarjima qilish",  "📚 Lug'atim"],
        ["🎯 Quiz / Test",     "⚙️ Sozlamalar"],
        ["📊 Statistika",      "❓ Yordam"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, input_field_placeholder="Tarjima uchun matn yozing...")


# ──────────────────────────────────────────────────────────────────────────────
# Language picker (inline)
# ──────────────────────────────────────────────────────────────────────────────
def language_picker_kb(callback_prefix: str, selected: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    callback_prefix: e.g. "tgt_lang" → callback_data = "tgt_lang:en"
    """
    items = list(LANGUAGES.items())
    rows: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    for code, info in items:
        label = f"{info['flag']} {info['native']}"
        if code == selected:
            label = f"✅ {label}"
        row.append(
            InlineKeyboardButton(label, callback_data=f"{callback_prefix}:{code}")
        )
        if len(row) == LANG_KEYBOARD_COLUMNS:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Post-translation actions
# ──────────────────────────────────────────────────────────────────────────────
def translation_actions_kb(
    original: str,
    translation: str,
    src: str,
    tgt: str,
) -> InlineKeyboardMarkup:
    import urllib.parse
    enc_orig = urllib.parse.quote(original[:60])
    enc_tran = urllib.parse.quote(translation[:60])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💾 Lug'atga saqlash", callback_data=f"save_word:{src}:{tgt}:{enc_orig}:{enc_tran}"),
        ],
        [
            InlineKeyboardButton("🔄 Boshqa tilga",     callback_data="change_target"),
            InlineKeyboardButton("🔁 Qayta tarjima",    callback_data="retranslate"),
        ],
    ])


# ──────────────────────────────────────────────────────────────────────────────
# Settings keyboard
# ──────────────────────────────────────────────────────────────────────────────
def settings_kb(source_lang: str, target_lang: str) -> InlineKeyboardMarkup:
    from services.translator import lang_display
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📥 Manba: {lang_display(source_lang)}", callback_data="set_source")],
        [InlineKeyboardButton(f"📤 Maqsad: {lang_display(target_lang)}", callback_data="set_target")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back:main")],
    ])


# ──────────────────────────────────────────────────────────────────────────────
# Vocabulary list pagination
# ──────────────────────────────────────────────────────────────────────────────
def vocab_list_kb(
    words: list,
    page: int,
    total: int,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []

    for w in words:
        rows.append([
            InlineKeyboardButton(
                f"🗑 #{w['id']}  {w['original'][:20]}",
                callback_data=f"del_word:{w['id']}",
            )
        ])

    # Pagination row
    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"vocab_page:{page - 1}"))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"vocab_page:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Quiz keyboards
# ──────────────────────────────────────────────────────────────────────────────
def quiz_languages_kb(has_user_vocab: bool = False) -> InlineKeyboardMarkup:
    """Inline keyboard for choosing a language for the quiz."""
    from data.quiz_words import QUIZ_LANGUAGES

    rows: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    for code, info in QUIZ_LANGUAGES.items():
        label = f"{info['flag']} {info['name']}"
        row.append(InlineKeyboardButton(label, callback_data=f"quiz_lang:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if has_user_vocab:
        rows.append([InlineKeyboardButton("📚 Shaxsiy lug'atimdan test", callback_data="quiz_lang:my_vocab")])

    rows.append([InlineKeyboardButton("🔙 Bosh menyu", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


def quiz_options_kb(options: List[str]) -> InlineKeyboardMarkup:
    """Multiple choice options for a quiz question."""
    rows = [
        [InlineKeyboardButton(f"{chr(65 + i)})  {opt}", callback_data=f"quiz_ans:{i}")]
        for i, opt in enumerate(options)
    ]
    rows.append([
        InlineKeyboardButton("⏭ O'tkazish", callback_data="quiz_skip"),
        InlineKeyboardButton("🛑 To'xtatish", callback_data="quiz_stop"),
    ])
    return InlineKeyboardMarkup(rows)


def quiz_finished_kb(lang_code: str) -> InlineKeyboardMarkup:
    """Post-quiz action buttons."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Yana test topshirish", callback_data=f"quiz_retry:{lang_code}")],
        [InlineKeyboardButton("🌐 Boshqa tilni tanlash", callback_data="quiz_change_lang")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="back:main")],
    ])


# ──────────────────────────────────────────────────────────────────────────────
# Confirm deletion
# ──────────────────────────────────────────────────────────────────────────────
def confirm_delete_kb(vocab_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha, o'chir", callback_data=f"confirm_del:{vocab_id}"),
            InlineKeyboardButton("❌ Bekor",      callback_data="back:vocab"),
        ]
    ])
