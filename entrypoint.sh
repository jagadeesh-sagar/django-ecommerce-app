#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations to RDS..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Daphne server..."
exec "$@"