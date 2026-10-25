from datetime import datetime, timedelta
import re

def parse_reminder(text: str):
    text_lower = text.lower().strip()
    
    for prefix in ["/remind", "напомни", "напомнить"]:
        if text_lower.startswith(prefix):
            text_lower = text_lower[len(prefix):].strip()

    # Получаем текущее время UTC и прибавляем 5 часов (Екатеринбург)
    now = datetime.utcnow() + timedelta(hours=5)
    
    remind_time = None
    date_found = False

    date_match_full = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', text_lower)
    date_match_short = re.search(r'\b(\d{1,2})\.(\d{1,2})\b', text_lower)

    if date_match_full:
        day = int(date_match_full.group(1))
        month = int(date_match_full.group(2))
        year = int(date_match_full.group(3))
        date_found = True
        time_match = re.search(r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9])\b', text_lower)
        hour = int(time_match.group(1)) if time_match else 12
        minute = int(time_match.group(2)) if time_match else 0
        try:
            remind_time = datetime(year, month, day, hour, minute)
        except ValueError:
            return None 
    elif date_match_short:
        day = int(date_match_short.group(1))
        month = int(date_match_short.group(2))
        date_found = True
        time_match = re.search(r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9])\b', text_lower)
        hour = int(time_match.group(1)) if time_match else 12
        minute = int(time_match.group(2)) if time_match else 0
        try:
            remind_time = datetime(now.year, month, day, hour, minute)
            if remind_time < now:
                remind_time = datetime(now.year + 1, month, day, hour, minute)
        except ValueError:
            return None

    if not remind_time and not date_found:
        time_match = re.search(r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9])\b', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if remind_time < now:
                remind_time += timedelta(days=1)

    if not remind_time and not date_found:
        time_words = re.search(r'в\s+(\d{1,2})\s*(утра|дня|вечера|ночи)', text_lower)
        if time_words:
            hour = int(time_words.group(1))
            part = time_words.group(2)
            if part in ["дня", "вечера"] and hour < 12: hour += 12
            if part == "ночи" and hour == 12: hour = 0
            remind_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if remind_time < now: remind_time += timedelta(days=1)

    if not remind_time and not date_found:
        delta_match = re.search(r'через\s+(\d+)\s*(минут|час)', text_lower)
        if delta_match:
            amount = int(delta_match.group(1))
            unit = delta_match.group(2)
            if "минут" in unit: remind_time = now + timedelta(minutes=amount)
            else: remind_time = now + timedelta(hours=amount)

    if not remind_time:
        return None

    if not date_found:
        if "послезавтра" in text_lower: remind_time += timedelta(days=2)
        elif "завтра" in text_lower: remind_time += timedelta(days=1)

    clean_text = text_lower
    clean_text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', '', clean_text)
    clean_text = re.sub(r'\b(\d{1,2})\.(\d{1,2})\b', '', clean_text)
    clean_text = re.sub(r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9])\b', '', clean_text)
    clean_text = re.sub(r'через\s+\d+\s*(минут|час)[а-я]*', '', clean_text)
    clean_text = re.sub(r'в\s+\d{1,2}\s*(утра|дня|вечера|ночи)', '', clean_text)
    
    stop_words = ["завтра", "послезавтра", "сегодня", "напомни", "пожалуйста", "мне", "меня", "в"]
    words = clean_text.split()
    final_words = [w for w in words if w not in stop_words]
    reminder_text = " ".join(final_words).strip()
    if not reminder_text: reminder_text = "Напоминание"

    return remind_time, reminder_text