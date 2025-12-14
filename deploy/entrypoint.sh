#!/usr/bin/env bash
set -e

python manage.py migrate --noinput

gunicorn antkeeping_guide.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level info &

nginx -g "daemon off;"
