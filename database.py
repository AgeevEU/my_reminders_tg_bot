import sqlite3
from datetime import datetime, timedelta

DB_PATH = "reminders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            repeat_type TEXT DEFAULT 'none',
            repeat_value INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_reminder(user_id: int, text: str, remind_at: datetime, repeat_type: str = 'none', repeat_value: int = 0):
    if repeat_type == 'weekly':
        days_ahead = repeat_value - remind_at.weekday()
        if days_ahead <= 0: days_ahead += 7
        remind_at += timedelta(days=days_ahead)
    elif repeat_type == 'monthly':
        if remind_at.day != repeat_value:
            if repeat_value > remind_at.day:
                remind_at = remind_at.replace(day=repeat_value)
            else:
                next_month = remind_at.month + 1
                next_year = remind_at.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                try:
                    remind_at = remind_at.replace(year=next_year, month=next_month, day=repeat_value)
                except ValueError:
                    remind_at += timedelta(days=30)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (user_id, text, remind_at, repeat_type, repeat_value) VALUES (?, ?, ?, ?, ?)",
        (user_id, text, remind_at.strftime("%Y-%m-%d %H:%M"), repeat_type, repeat_value)
    )
    conn.commit()
    conn.close()

def get_user_reminders(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, text, remind_at, repeat_type, repeat_value FROM reminders "
        "WHERE user_id = ? AND sent = 0 ORDER BY remind_at",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_due_reminders():
    # Берем текущее время UTC и прибавляем 5 часов (время Екатеринбурга)
    now_ekb = datetime.utcnow() + timedelta(hours=5)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, text, repeat_type, repeat_value, remind_at FROM reminders "
        "WHERE sent = 0"
    )
    rows = cur.fetchall()
    conn.close()
    
    due_reminders = []
    for row in rows:
        rid, user_id, text, r_type, r_val, remind_at_str = row
        
        # Время в базе уже хранится как Екатеринбургское
        remind_at = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M")
        
        # Если время пришло — добавляем в список
        if remind_at <= now_ekb:
            due_reminders.append((rid, user_id, text, r_type, r_val, remind_at_str))
            
    return due_reminders

def reschedule_or_mark(reminder_id: int, repeat_type: str, repeat_value: int, old_time_str: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    old_time = datetime.strptime(old_time_str, "%Y-%m-%d %H:%M")
    
    if repeat_type == 'none':
        cur.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
    elif repeat_type == 'daily':
        new_time = old_time + timedelta(days=1)
        cur.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", (new_time.strftime("%Y-%m-%d %H:%M"), reminder_id))
    elif repeat_type == 'weekly':
        days_ahead = repeat_value - old_time.weekday()
        if days_ahead <= 0: days_ahead += 7
        new_time = old_time + timedelta(days=days_ahead)
        cur.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", (new_time.strftime("%Y-%m-%d %H:%M"), reminder_id))
    elif repeat_type == 'monthly':
        next_month = old_time.month + 1
        next_year = old_time.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        try:
            new_time = old_time.replace(year=next_year, month=next_month, day=repeat_value)
        except ValueError:
            new_time = old_time + timedelta(days=30) 
        cur.execute("UPDATE reminders SET remind_at = ? WHERE id = ?", (new_time.strftime("%Y-%m-%d %H:%M"), reminder_id))
        
    conn.commit()
    conn.close()

def delete_reminder(list_index: int, user_id: int):
    reminders = get_user_reminders(user_id)
    if list_index < 1 or list_index > len(reminders):
        return False
    real_db_id = reminders[list_index - 1][0]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?", (real_db_id, user_id))
    conn.commit()
    conn.close()
    return True