import logging
import os

from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

# подключение к MongoDB
client = MongoClient(MONGO_URI)

# выбор базы данных
db = client["my_local_database"]

# выбор коллекции
collection = db["user"]

# Настройка логгера
logger = logging.getLogger(__name__)


# def add_coin_to_active(chat_id, coin, exchange):
#     exchange_key = "BYBIT" if exchange.lower() == 'bybit' else "BINANCE"
#
#     user = collection.find_one({"chat_id": chat_id})
#
#     if user:
#         # Проверяем, есть ли уже данные для этой биржи
#         exchange_data = next((e for e in user["exchange"] if e["exchange"] == exchange_key), None)
#
#         if exchange_data:
#             # Если данные для биржи существуют, добавляем монету
#             collection.update_one(
#                 {"chat_id": chat_id, "exchange.exchange": exchange_key},
#                 {"$push": {"exchange.$.active_coins": coin}}
#             )
#             logger.info(f"Монета {coin} успешно добавлена в активные монеты для пользователя {chat_id} на бирже {exchange_key}.")
#         else:
#             # Если данных для этой биржи нет, создаем запись для новой биржи
#             collection.update_one(
#                 {"chat_id": chat_id},
#                 {"$push": {"exchange": {"exchange": exchange_key, "active_coins": [coin]}}}
#             )
#             logger.info(f"Биржа {exchange_key} добавлена для пользователя {chat_id} с монетой {coin}.")
#     else:
#         # Если пользователь не найден, создаем нового пользователя с биржей и монетой
#         user_data = {
#             "chat_id": chat_id,
#             "exchange": [{"exchange": exchange_key, "active_coins": [coin]}]
#         }
#         collection.insert_one(user_data)
#         logger.info(f"Пользователь {chat_id} добавлен в базу с биржей {exchange_key} и монетой {coin}.")


# Извлечение списка активных монет с фильтром по бирже
def get_active_coins(chat_id, exchange):
    exchange_key = "BYBIT" if exchange.lower() == 'bybit' else "BINANCE"

    # Находим пользователя и конкретную биржу в массиве exchanges
    user = collection.find_one(
        {"chat_id": chat_id, "exchange.exchange": exchange_key},
        {"exchange.$": 1, "_id": 0}
    )

    if user and "exchange" in user:
        exchange_data = user["exchange"][0]
        return exchange_data["active_coins"]
    else:
        return []  # пустой список

#
# # Удаление неактивных монет
# def remove_inactive_coins(chat_id, exchange, inactive_coin):
#     inactive_coin = inactive_coin.strip()
#
#     # регулярное выражение для поиска монет, содержащих часть inactive_coin
#     regex = re.compile(f".*{re.escape(inactive_coin)}.*", re.IGNORECASE)
#
#     result = collection.update_one(
#         {"chat_id": chat_id, "exchange.exchange": exchange},
#         {"$pull": {"exchange.$.active_coins": {"$regex": regex}}}
#     )
#
#     if result.matched_count > 0:
#         if result.modified_count > 0:
#             logger.info(f"Монета или монеты, содержащие {inactive_coin}, успешно удалены из активных монет для пользователя {chat_id} на бирже {exchange}.")
#         else:
#             logger.info(f"Монета, содержащая {inactive_coin}, не была удалена, потому что её не было в массиве.")
#     else:
#         logger.info(f"Не найден пользователь с chat_id {chat_id} и биржей {exchange}.")



