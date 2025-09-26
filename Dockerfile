FROM python:3.13-slim

# Определяем переменные окружения
ENV HOST=0.0.0.0 \
    PORT=5001 \
    TELEGRAM_TOKEN="7654837384:AAGcOdX5jzGv1ZTNqPT8vlY0rwLsL-w5STA" \
    ROBOT_URL_BTCUSDT_BYBIT="" \
    ROBOT_URL_LTCUSDT_BYBIT="" \
    ROBOT_URL_BTCUSDT_BINANCE2="" \
    ROBOT_URL_STORJUSDT_BINANCE2="" \
    ROBOT_URL_BNBUSDT_BINANCE2="" \
    ROBOT_URL_LTCUSDT_BINANCE2=""

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libatlas3-base \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /bot
ENV PYTHONPATH "${PYTHONPATH}:/bot/"

# Копируем файл зависимостей в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код в рабочую директорию
COPY app ./app

# Определяем команду по умолчанию для запуска приложения
CMD ["python", "/bot/app/run.py"]
