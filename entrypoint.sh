#!/bin/sh

echo "Waiting for database..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "Database is up!"

python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput

exec "$@"
