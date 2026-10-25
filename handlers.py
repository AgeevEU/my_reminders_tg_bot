from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from parser import parse_reminder
from database import add_reminder, get_user_reminders, delete_reminder

router = Router()
pending_reminders = {}

@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Я умею ставить напоминания.\n\n"
        "Пример: напомни завтра в 18:00 купить хлеб\n\n"
        "Команды:\n"
        "/list или «список» — все напоминания\n"
        "/delete номер или «удалить номер» — удалить",
        parse_mode="Markdown"
    )

def format_beautiful_date(remind_at_str: str) -> str:
    dt_obj = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M")
    # Берем сегодняшнюю дату по Екатеринбургу
    now_ekb = datetime.utcnow() + timedelta(hours=5)
    
    if dt_obj.date() == now_ekb.date(): date_str = "Сегодня"
    elif dt_obj.date() == now_ekb.date() + timedelta(days=1): date_str = "Завтра"
    elif dt_obj.date() == now_ekb.date() + timedelta(days=2): date_str = "Послезавтра"
    else:
        date_str = dt_obj.strftime("%d.%m") if dt_obj.year == now_ekb.year else dt_obj.strftime("%d.%m.%Y")
    return f"{date_str} в {dt_obj.strftime('%H:%M')}"

def build_list_text(user_id):
    rows = get_user_reminders(user_id)
    if not rows:
        return "📭 У вас нет активных напоминаний."
    answer = "📋 Ваши напоминания:\n\n"
    for index, (rid, text, remind_at, r_type, r_val) in enumerate(rows, start=1):
        icon = "🔁" if r_type != 'none' else ""
        answer += f"{index}. {text.capitalize()} — {format_beautiful_date(remind_at)} {icon}\n"
    return answer

@router.message(Command("list"))
@router.message(F.text.lower().in_(["список", "мои напоминания", "мои дела", "дела", "задачи", "мои задачи", "что по плану", "план", "планы", "лист"]))
async def list_reminders(message: Message):
    text = build_list_text(message.from_user.id)
    await message.answer(text)

@router.message(Command("delete"))
@router.message(F.text.lower().startswith(("удалить", "удали", "стереть", "сотри", )))
async def delete(message: Message):
    try:
        parts = message.text.split()
        list_index = int(parts[1])
        if delete_reminder(list_index, message.from_user.id):
            new_list_text = build_list_text(message.from_user.id)
            await message.answer(f"🗑 Напоминание №{list_index} удалено.\n\n{new_list_text}")
        else:
            await message.answer("❌ Такого номера нет. Напишите «список», чтобы проверить.")
    except (IndexError, ValueError):
        await message.answer("❌ Напишите: удалить 1")

@router.message(F.text.regexp(r'^\d{1,2}$'))
async def save_month_repeat(message: Message):
    user_id = message.from_user.id
    if user_id not in pending_reminders: return
    day_num = int(message.text)
    if not (1 <= day_num <= 31):
        await message.answer("Число должно быть от 1 до 31. Попробуй еще раз.")
        return
    data = pending_reminders[user_id]
    add_reminder(user_id, data['text'], data['dt'], repeat_type='monthly', repeat_value=day_num)
    del pending_reminders[user_id]
    await message.answer(f"✅ Напоминание добавлено!\n\n📝 {data['text'].capitalize()}\n📅 {format_beautiful_date(data['dt'].strftime('%Y-%m-%d %H:%M'))}\n🔁 Каждое {day_num} число")

@router.message()
async def handle_text(message: Message):
    if message.text.lower() in ["список", "мои напоминания", "мои дела", "дела", "задачи", "мои задачи", "что по плану", "план", "планы", "лист"]:
        return
    result = parse_reminder(message.text)
    if not result:
        await message.answer("🤔 Не понял время. Пример: «напомни завтра в 18:00 купить хлеб»")
        return
    dt, text = result
    
    # Проверяем, не прошло ли время (по Екатеринбургу)
    now_ekb = datetime.utcnow() + timedelta(hours=5)
    if dt < now_ekb:
        await message.answer("⏰ Это время уже прошло.")
        return
        
    pending_reminders[message.from_user.id] = {"dt": dt, "text": text}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Один раз", callback_data="rep_none")],
        [InlineKeyboardButton(text="🔁 Каждый день", callback_data="rep_daily")],
        [InlineKeyboardButton(text="📅 По дням недели", callback_data="rep_week")],
        [InlineKeyboardButton(text="🔢 В число месяца", callback_data="rep_month")]
    ])
    await message.answer(
        f"Ты хочешь добавить:\n📝 *{text.capitalize()}*\n📅 {format_beautiful_date(dt.strftime('%Y-%m-%d %H:%M'))}\n\nКак часто это повторять?",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.in_(["rep_none", "rep_daily"]))
async def process_simple_repeat(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in pending_reminders: return
    data = pending_reminders[user_id]
    r_type = 'none' if callback.data == "rep_none" else 'daily'
    add_reminder(user_id, data['text'], data['dt'], repeat_type=r_type)
    del pending_reminders[user_id]
    repeat_msg = "\n🔁 Каждый день" if r_type == 'daily' else ""
    await callback.message.edit_text(f"✅ Напоминание добавлено!\n\n📝 {data['text'].capitalize()}\n📅 {format_beautiful_date(data['dt'].strftime('%Y-%m-%d %H:%M'))}{repeat_msg}")

@router.callback_query(F.data == "rep_week")
async def process_week_repeat(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Понедельник", callback_data="w_0")],
        [InlineKeyboardButton(text="Вторник", callback_data="w_1")],
        [InlineKeyboardButton(text="Среда", callback_data="w_2")],
        [InlineKeyboardButton(text="Четверг", callback_data="w_3")],
        [InlineKeyboardButton(text="Пятница", callback_data="w_4")],
        [InlineKeyboardButton(text="Суббота", callback_data="w_5")],
        [InlineKeyboardButton(text="Воскресенье", callback_data="w_6")]
    ])
    await callback.message.edit_text("Выбери день недели для повторения:", reply_markup=kb)

@router.callback_query(F.data.startswith("w_"))
async def save_week_repeat(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in pending_reminders: return
    day_index = int(callback.data.split("_")[1])
    data = pending_reminders[user_id]
    add_reminder(user_id, data['text'], data['dt'], repeat_type='weekly', repeat_value=day_index)
    del pending_reminders[user_id]
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    await callback.message.edit_text(f"✅ Напоминание добавлено!\n\n📝 {data['text'].capitalize()}\n📅 {format_beautiful_date(data['dt'].strftime('%Y-%m-%d %H:%M'))}\n🔁 Каждый {days_ru[day_index]}")

@router.callback_query(F.data == "rep_month")
async def process_month_repeat(callback: CallbackQuery):
    await callback.message.edit_text("Напиши в чат число месяца (например: 15), и я сохраню напоминание.")