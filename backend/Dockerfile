# Используем Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы бэкенда
COPY . /app

# Устанавливаем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Указываем порт для экспозиции
EXPOSE 5000

# Команда для запуска приложения
CMD ["python", "app.py"]