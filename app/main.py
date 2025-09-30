import logging
import os
import threading
import time
import requests

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from telebot import TeleBot

from app.const.messages import msg_start, msg_help, msg_error_coin

# -----------------------
# Конфиг через env
# -----------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5001))

ROBOT_URLS = {
    "BTCUSDT": os.environ.get("ROBOT_URL_BTCUSDT", "http://127.0.0.1:5002"),
    "ETHUSDT": os.environ.get("ROBOT_URL_ETHUSDT", "http://127.0.0.1:5003"),
    "SOLUSDT": os.environ.get("ROBOT_URL_SOLUSDT", "http://127.0.0.1:5004"),
    "XRPUSDT": os.environ.get("ROBOT_URL_XRPUSDT", "http://127.0.0.1:5005"),
    "MNTUSDT": os.environ.get("ROBOT_URL_MNTUSDT", "http://127.0.0.1:5006"),
}

# -----------------------
# Логирование
# -----------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен.")

# -----------------------
# Инициализация бота
# -----------------------
bot = TeleBot(TELEGRAM_TOKEN)


def run_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(15)


threading.Thread(target=run_polling, daemon=True).start()

# -----------------------
# FastAPI
# -----------------------
app = FastAPI()


# -----------------------
# Команды
# -----------------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, msg_start)


@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, msg_help)


@bot.message_handler(commands=['trade'])
def trade_cmd(message):
    msg = bot.send_message(message.chat.id, "Введите тикер для запуска торговли:")
    bot.register_next_step_handler(msg, process_run_step)


@bot.message_handler(commands=['stop_trade'])
def stop_trade_cmd(message):
    msg = bot.send_message(message.chat.id, "Введите тикер для остановки торговли:")
    bot.register_next_step_handler(msg, process_stop_step)


# -----------------------
# Обработка ввода
# -----------------------
def process_run_step(message):
    chat_id = message.chat.id
    coin = message.text.upper()

    if coin not in ROBOT_URLS:
        bot.send_message(chat_id, msg_error_coin)
        return

    bot.send_message(chat_id, f"Запуск торговли для {coin}...")
    send_config_to_robot(chat_id, coin, True)


def process_stop_step(message):
    chat_id = message.chat.id
    coin = message.text.upper()

    if coin not in ROBOT_URLS:
        bot.send_message(chat_id, msg_error_coin)
        return

    bot.send_message(chat_id, f"Остановка торговли для {coin}...")
    send_config_to_robot(chat_id, coin, False)


# -----------------------
# Отправка конфигурации роботу
# -----------------------
def send_config_to_robot(chat_id, coin, is_start: bool):
    try:
        url = f"{ROBOT_URLS[coin]}/config/BYBIT/{coin}"
        response = requests.post(url, json={'chat_id': chat_id, 'is_start': is_start})
        response.raise_for_status()
        status = "запущена" if is_start else "остановлена"
        bot.send_message(chat_id, f"Торговля для {coin} {status}.")
    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"Ошибка при отправке команды: {e}")


# -----------------------
# Эндпоинт для данных от робота
# -----------------------
@app.post('/robot_data')
async def receive_data(data: dict):
    chat_id = data.get('chat_id')
    message = data.get('message')

    if chat_id and message:
        try:
            image_path = None
            if "Продажа" in message:
                image_path = "imgs/sell.png"
            elif "Покупка" in message:
                image_path = "imgs/buy.png"

            if image_path:
                absolute_path = os.path.join(os.getcwd(), image_path)
                if not os.path.exists(absolute_path):
                    logger.error(f"Файл {absolute_path} не найден")
                    raise HTTPException(status_code=500, detail=f"File {absolute_path} not found")

                with open(absolute_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo=photo, caption=message)
            else:
                bot.send_message(chat_id, message)

            return JSONResponse(content={"status": "success", "message": "Message sent to user"}, status_code=200)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Invalid data")


@app.get("/")
async def root():
    return {"message": "API is working"}
