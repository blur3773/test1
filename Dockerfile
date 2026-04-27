# Dockerfile для Книжного магазина API
FROM python:3.11-slim

# Рабочая директория в контейнере
WORKDIR /app

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директории для базы данных
RUN mkdir -p /app/instance

# Порт приложения
EXPOSE 5001

# Команда запуска
CMD ["python", "main.py"]
