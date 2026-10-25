import os
import threading
from flask import Flask
from bot import main as start_bot  # Импортируем функцию запуска бота

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running"

def run_bot():
    import asyncio
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Запускаем бота в фоне
    threading.Thread(target=run_bot, daemon=True).start()
    # Запускаем Flask, чтобы Render видел открытый порт
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
