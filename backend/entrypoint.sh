#!/bin/bash
echo "[+] Creating migrations"
python manage.py makemigrations

echo "[+] Applying migrations"
python manage.py migrate

echo "[+] Collecting static files"
python manage.py collectstatic --noinput

echo "[+] Starting server"
exec "$@"
