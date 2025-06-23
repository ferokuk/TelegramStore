FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app/backend

COPY requirements.txt /app/backend/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

copy . /app/backend/

EXPOSE 8000

RUN chmod +x /app/backend/entrypoint.sh

ENTRYPOINT ["sh", "/app/backend/entrypoint.sh"]

CMD ["uvicorn", "TelegramStore.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers 3"]
