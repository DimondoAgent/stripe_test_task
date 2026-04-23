#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate

echo "Loading fixtures if DB is empty..."
python manage.py shell -c "
from shop.models import Item
from django.core.management import call_command
if not Item.objects.exists():
    call_command('loaddata', 'initial_data.json')
    print('Fixture loaded.')
else:
    print('Skipping fixture, DB already has data.')
"

echo "Starting Gunicorn..."
exec gunicorn stripe_shop.wsgi:application --bind 0.0.0.0:8000 --workers 2
