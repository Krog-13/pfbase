#!/bin/bash

echo "RUN_MIGRATIONS is: $RUN_MIGRATIONS"
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "RUN_MIGRATIONS is true, executing migrations..."
  python manage.py create_schema
  python manage.py makemigrations users
  python manage.py makemigrations documents
  python manage.py makemigrations dictionaries
  python manage.py migrate --no-input
  python manage.py create_superuser
else
  echo "RUN_MIGRATIONS is not set to true, skipping migrations."
fi

gunicorn IEF.wsgi:application --bind 0.0.0.0:8000