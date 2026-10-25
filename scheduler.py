from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_due_reminders, reschedule_or_mark

scheduler = AsyncIOScheduler()

async def check_reminders(bot):
    due = get_due_reminders()
    for rid, user_id, text, repeat_type, repeat_value, old_time in due:
        try:
            prefix = "🔁 " if repeat_type != 'none' else ""
            await bot.send_message(user_id, f"🔔 Напоминание!\n\n{prefix}📝 {text}")
            reschedule_or_mark(rid, repeat_type, repeat_value, old_time)
        except Exception as e:
            print(f"Ошибка отправки: {e}")

def start_scheduler(bot):
    scheduler.add_job(check_reminders, "interval", minutes=1, args=[bot])
    scheduler.start()