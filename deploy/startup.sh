#!/bin/bash
set -e

echo "==> Starting Enigma App on Azure..."

# Wait for database if needed and run migrations
echo "==> Applying database migrations..."
python manage.py migrate --noinput

# Collect static files with WhiteNoise compression
echo "==> Collecting static assets..."
python manage.py collectstatic --noinput

# Seed default admin and sample data if needed (optional check)
if [ "$AUTO_SEED_DATA" = "True" ]; then
    echo "==> Running automated database seeding..."
    python manage.py seed_data || true
fi

# Start Gunicorn WSGI server
echo "==> Starting Gunicorn server on 0.0.0.0:8000..."
exec gunicorn club_attendance.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
