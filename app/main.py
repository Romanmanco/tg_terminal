import threading
import time

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from app.const.messages import *
from storage.mongo import *

# Получение конфига через переменные окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = os.environ.get("PORT", "5001")
# http://172.17.0.2:5003
ROBOT_URL_BTCUSDT_BYBIT = os.environ.get("ROBOT_URL_BTCUSDT_BYBIT", "http://127.0.0.1:5002")
ROBOT_URL_LTCUSDT_BYBIT = os.environ.get("ROBOT_URL_LTCUSDT_BYBIT", "http://127.0.0.1:5002")
ROBOT_URL_XRPUSDT_BYBIT = os.environ.get("ROBOT_URL_XRPUSDT_BYBIT", "")
ROBOT_URL_ETHUSDT_BYBIT = os.environ.get("ROBOT_URL_ETHUSDT_BYBIT", "")
ROBOT_URL_DOGEUSDT_BYBIT = os.environ.get("ROBOT_URL_DOGEUSDT_BYBIT", "")
ROBOT_URL_SOLUSDT_BYBIT = os.environ.get("ROBOT_URL_SOLUSDT_BYBIT", "")

# ROBOT_URL_BTCUSDT_BINANCE = os.environ.get("ROBOT_URL_BTCUSDT_BINANCE", "")
# ROBOT_URL_BNBUSDT_BINANCE = os.environ.get("ROBOT_URL_BNBUSDT_BINANCE", "http://172.17.0.2:5003")
# ROBOT_URL_LTCUSDT_BINANCE = os.environ.get("ROBOT_URL_LTCUSDT_BINANCE", "")
# ROBOT_URL_ETHUSDT_BINANCE = os.environ.get("ROBOT_URL_ETHUSDT_BINANCE", "")
# ROBOT_URL_DOGEUSDT_BINANCE = os.environ.get("ROBOT_URL_DOGEUSDT_BINANCE", "")
# ROBOT_URL_SOLUSDT_BINANCE = os.environ.get("ROBOT_URL_SOLUSDT_BINANCE", "")

# Глобальные переменные
robot_urls = {
    "BYBIT": {
        "BTCUSDT": ROBOT_URL_BTCUSDT_BYBIT,
        "LTCUSDT": ROBOT_URL_LTCUSDT_BYBIT,
        "XRPUSDT": ROBOT_URL_XRPUSDT_BYBIT,
        "ETHUSDT": ROBOT_URL_ETHUSDT_BYBIT,
        "DOGEUSDT": ROBOT_URL_DOGEUSDT_BYBIT,
        "SOLUSDT": ROBOT_URL_SOLUSDT_BYBIT,
    },
    # "BINANCE": {
    #     "BTCUSDT": ROBOT_URL_BTCUSDT_BINANCE,
    #     "BNBUSDT": ROBOT_URL_BNBUSDT_BINANCE,
    #     "LTCUSDT": ROBOT_URL_LTCUSDT_BINANCE,
    #     "ETHUSDT": ROBOT_URL_ETHUSDT_BINANCE,
    #     "DOGEUSDT": ROBOT_URL_DOGEUSDT_BINANCE,
    #     "SOLUSDT": ROBOT_URL_SOLUSDT_BINANCE,
    # },
}
valid_id = [
    "iowesdsffsfssg",
    # "faskoaojaoioao",
    # "ksalfkslfsa;la",
    # "sdkgklsgkl;sss",
    # "sfsfsfssfsffhj",
]
blocked = True
user_data = {
    "user_personal_id": "",
    "chat_id": "",
}
active_trades = {}


# Добавление лога
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен.")

# Инициализация бота
bot = TeleBot(TELEGRAM_TOKEN)

# Запуск polling в отдельном потоке
def run_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(15)  # пауза перед повторным запуском


# polling
bot_thread = threading.Thread(target=run_polling)
bot_thread.start()


app = FastAPI()

def is_valid_user(chat_id):
    user = collection.find_one({"chat_id": chat_id})
    return user is not None

# Команды бота
@bot.message_handler(commands=['start'])
def start_cmd(message):
    global blocked
    chat_id = message.chat.id
    logger.info(f"Использована команда /start пользователем: {chat_id}")

    # проверка на допустимость пользователя
    if is_valid_user(chat_id):
        bot.send_message(chat_id=chat_id, text=msg_registered)
        bot.send_message(chat_id=chat_id, text=msg_start)
        blocked = False
    else:
        if collection.count_documents({}) < len(valid_id):  # количество пользователей
            # проверка наличие chat_id в valid_id
            user_personal_id = next((id for id in valid_id if id not in collection.distinct("user_personal_id")), None)
            if user_personal_id:
                # новый объект данных для пользователя, чтобы избежать повторного использования одного и того же _id
                new_user_data = user_data.copy()
                new_user_data.update({"chat_id": chat_id})
                new_user_data.update({"user_personal_id": user_personal_id})
                collection.insert_one(new_user_data)
                bot.send_message(chat_id=chat_id, text=msg_success_registered)
                logger.info(f"Пользователь с chat_id {chat_id} зарегистрирован.")
                bot.send_message(chat_id=chat_id, text=msg_start)
                blocked = False
            else:
                bot.send_message(chat_id=chat_id, text=msg_error_user)
                logger.warning(f"Пользователь с chat_id {chat_id} попытался зарегистрироваться, но достигнут лимит.")
                blocked = True
        else:
            bot.send_message(chat_id=chat_id, text=msg_error_user)
            logger.warning(f"Пользователь с chat_id {chat_id} попытался зарегистрироваться, но достигнут лимит.")
            blocked = True
    if not blocked:
        # добавление кнопок Trade и Stop Trade
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Trade"), KeyboardButton("Stop Trade"), KeyboardButton("Active coins"))
        bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help_cmd(message):
    logger.info(f"Использована команда /help пользователем: {message.chat.id}")
    bot.send_message(message.chat.id, msg_help)


@bot.message_handler(func=lambda message: message.text == "Trade")
def trade_cmd(message):
    global blocked
    if not blocked:
        logger.info(f"Использована команда Trade пользователем: {message.chat.id}")
        chat_id = message.chat.id
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Bybit", callback_data='start_bybit'))
        keyboard.add(InlineKeyboardButton("Binance(Sub-akk)", callback_data='start_binance'))
        bot.send_message(chat_id=chat_id, text=msg_chose_exchange, reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "Stop Trade")
def stop_trade_cmd(message):
    global blocked
    if not blocked:
        logger.info(f"Использована команда Stop_trade пользователем: {message.chat.id}")
        chat_id = message.chat.id

        # Получение активных монет для пользователя
        # active_bybit = active_trades.get(chat_id, {}).get("BYBIT", [])
        # active_binance = active_trades.get(chat_id, {}).get("BINANCE", [])
        active_bybit = get_active_coins(chat_id, "BYBIT")
        active_binance = get_active_coins(chat_id, "BINANCE")

        # Если нет активных монет, уведомление пользователя
        if not active_bybit and not active_binance:
            bot.send_message(chat_id=chat_id, text="У вас нет активных торговых пар.")
            return

        # Формирование сообщения с активными монетами
        message_text = "Активные монеты для остановки торговли:\n\n"
        if active_bybit:
            message_text += "Bybit:\n" + ', '.join(active_bybit) + "\n\n"  # Преобразуем список в строку
        if active_binance:
            message_text += "Binance:\n" + ', '.join(active_binance) + "\n"  # Преобразуем список в строку

        bot.send_message(chat_id=chat_id, text=message_text)

        # Кнопки для выбора биржи остановки торговли
        keyboard = InlineKeyboardMarkup()
        if active_bybit:
            keyboard.add(InlineKeyboardButton("Остановить Bybit", callback_data='stop_bybit'))
        if active_binance:
            keyboard.add(InlineKeyboardButton("Остановить Binance", callback_data='stop_binance'))

        bot.send_message(chat_id=chat_id, text="Выберите биржу для остановки торговли:", reply_markup=keyboard)


# @bot.message_handler(func=lambda message: message.text == "Active coins")
# def active_coins_cmd(message):
#     global blocked
#     if not blocked:
#         logger.info(f"Использована команда Active_coins пользователем: {message.chat.id}")
#         chat_id = message.chat.id
#
#         # Получение активных монет для пользователя
#         active_bybit = get_active_coins(chat_id, "BYBIT")
#         # active_binance = get_active_coins(chat_id, "BINANCE")
#
#         # Если нет активных монет, уведомление пользователя
#         if not active_bybit and not active_binance:
#             bot.send_message(chat_id=chat_id, text="У вас нет активных монет.")
#             return
#
#         # Формирование сообщения с активными монетами
#         message_text = "Ваши активные монеты:\n\n"
#
#         # Добавляем монеты для Bybit, если они есть
#         if active_bybit:
#             message_text += "Bybit:\n" + ', '.join(active_bybit) + "\n\n"  # Преобразуем список в строку
#         # if active_binance:
#         #     message_text += "Binance:\n" + ', '.join(active_binance) + "\n"  # Преобразуем список в строку
#
#         bot.send_message(chat_id=chat_id, text=message_text)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)

    if call.data == 'back_to_exchange_choice':
        bot.clear_step_handler(call.message)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Bybit", callback_data='start_bybit'))
        # keyboard.add(InlineKeyboardButton("Binance(Sub-akk)", callback_data='start_binance'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=msg_chose_exchange, reply_markup=keyboard)

    elif call.data == 'back_to_exchange_choice_stop':
        bot.clear_step_handler(call.message)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Bybit", callback_data='stop_bybit'))
        # keyboard.add(InlineKeyboardButton("Binance(Sub-akk)", callback_data='stop_binance'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=msg_chose_exchange, reply_markup=keyboard)

    # Логика для выбора Bybit
    elif call.data == 'start_bybit':
        bot.send_message(chat_id, "Запуск робота на байбит")
        msg = bot.send_message(chat_id, msg_trade)
        bot.register_next_step_handler(msg, process_run_step, "bybit")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Назад к выбору", callback_data='back_to_exchange_choice'))
        bot.send_message(chat_id, "Если хотите вернуться, нажмите 'Назад к выбору'.", reply_markup=keyboard)

    elif call.data == 'stop_bybit':
        msg = bot.send_message(chat_id, "Введите тикер для остановки:")
        bot.register_next_step_handler(msg, process_stop_step, "bybit")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Назад к выбору", callback_data='back_to_exchange_choice_stop'))
        bot.send_message(chat_id, "Если хотите вернуться, нажмите 'Назад к выбору'.", reply_markup=keyboard)


def process_run_step(message, exchange):
    chat_id = message.chat.id
    coin = str.upper(message.text)
    exchange_key = ""

    if exchange.lower() == 'bybit':
        exchange_key = "BYBIT"

    if len(coin) < 6:
        bot.send_message(chat_id=chat_id, text=msg_error_coin_run)
    elif coin not in robot_urls[exchange_key].keys():
        bot.send_message(chat_id=chat_id, text=msg_error_name_coin_run)
    else:
        bot.send_message(chat_id=chat_id, text=f"Вы ввели тикер: {coin}\nДля завершения работы робота используйте "
                                               f"команду: /stop_trade")
        send_config_to_robot_run(chat_id, exchange, coin)


def process_stop_step(message, exchange):
    chat_id = message.chat.id
    coin = str.upper(message.text)
    exchange_key = "BYBIT" if exchange.lower() == 'bybit' else "BINANCE"

    if len(coin) < 6:
        bot.send_message(chat_id=chat_id, text=msg_error_coin_stop)
    elif coin not in robot_urls[exchange_key].keys():
        bot.send_message(chat_id=chat_id, text=msg_error_name_coin_stop)
    else:
        bot.send_message(chat_id=chat_id, text=f"Монета: {coin}\nУдалена из списка.")
        send_config_to_robot_stop(chat_id, exchange, coin)


def send_config_to_robot_run(chat_id, exchange, coin_pair):
    try:
        if exchange.lower() == 'bybit':
            exchange_key = "BYBIT"
        else:
            bot.send_message(chat_id=chat_id, text="Неподдерживаемая биржа.")
            return

        if exchange_key in robot_urls and coin_pair in robot_urls[exchange_key]:
            url = robot_urls[exchange_key][coin_pair] + '/config/' + exchange_key + '/' + coin_pair

            response = requests.post(url, json={
                'chat_id': chat_id,
                'is_start': True
            })
            response.raise_for_status()

            # Добавление монеты в список активных торгов
            if chat_id not in active_trades:
                active_trades[chat_id] = {"BYBIT": [], "BINANCE": []}
            if coin_pair not in active_trades[chat_id][exchange_key]:
                active_trades[chat_id][exchange_key].append(coin_pair)

            logger.info(f"Данные успешно отправлены: {response.json()}")
        else:
            bot.send_message(chat_id=chat_id, text=msg_error_name_coin_run)
            logger.info(f"Неизвестная пара: {coin_pair}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке данных: {e}")
        bot.send_message(chat_id=chat_id, text=msg_error_command)


def send_config_to_robot_stop(chat_id, exchange, coin_pair):
    try:
        if exchange.lower() == 'bybit':
            exchange_key = "BYBIT"
        elif exchange.lower() == 'binance':
            exchange_key = "BINANCE"
        else:
            bot.send_message(chat_id=chat_id, text="Неподдерживаемая биржа.")
            return

        if exchange_key in robot_urls and coin_pair in robot_urls[exchange_key]:
            url = robot_urls[exchange_key][coin_pair] + '/config/' + exchange_key + '/' + coin_pair

            payload = {
                'chat_id': chat_id,
                'is_start': False,
            }
            logger.info(f"Отправляем данные: {payload}")
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Данные успешно отправлены: {response.json()}")
        else:
            bot.send_message(chat_id=chat_id, text=msg_error_name_coin_stop)
            logger.info(f"Неизвестная пара: {coin_pair}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке данных: {e}")
        bot.send_message(chat_id=chat_id, text=msg_error_command)


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

