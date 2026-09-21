#!/usr/bin/env bash
set -o errexit

rm -rf staticfiles
pip install -r requirements.txt
python manage.py collectstatic --no-input --clear
python manage.py migrate --noinput
python manage.py ensure_admin
