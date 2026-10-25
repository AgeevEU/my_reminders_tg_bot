import os
import threading
import asyncio
from flask import Flask
from bot import main as start_bot

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running"

def run_flask():
    # Запускаем Flask в фоновом режиме, чтобы он слушал порт
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    # 1. Запускаем Flask в фоне (он нужен Render для проверки порта)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # 2. Запускаем бота в ГЛАВНОМ потоке (чтобы aiogram не ругался на сигналы)
    asyncio.run(start_bot())
