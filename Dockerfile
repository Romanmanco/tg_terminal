FROM python:3.13-slim

# Определяем переменные окружения
ENV HOST=0.0.0.0 \
    PORT=5001 \
    TELEGRAM_TOKEN="7654837384:AAG484DRWxiRE6M5"

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libatlas3-base \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /bot
ENV PYTHONPATH="/bot:${PYTHONPATH}"

# Копируем файл зависимостей в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код в рабочую директорию
COPY app ./app

# Определяем команду по умолчанию для запуска приложения
CMD ["python", "/bot/app/run.py"]
