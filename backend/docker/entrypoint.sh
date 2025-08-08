#!/bin/bash

source .venv/bin/activate

echo "Check migrations..."
uv run python manage.py makemigrations

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

echo "Running database migrations..."
uv run python manage.py migrate --noinput

echo "Starting Django development server..."
uv run python manage.py runserver 0.0.0.0:8000
