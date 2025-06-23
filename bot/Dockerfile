FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

# Копируем зависимости бота
COPY requirements.txt .

# Устанавливаем зависимости бота
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install watchfiles
# Копируем код бота
COPY ./src ./src

CMD ["python", "-m", "src.main"]
