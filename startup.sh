#!/bin/bash
set -e

echo "Starting Enrico Backend..."

# Use Railway's PORT if available, fallback to 8000
APP_PORT=${PORT:-8000}

echo "Waiting for database connection..."
uv run python -c "
import time
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/enrico_cerrini_dev')

if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

print('Connecting to Database...')

# psycopg2 fully supports URI strings, even with postgres:// or postgresql://
max_attempts = 30
for i in range(max_attempts):
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print('Database connection successful!')
        break
    except Exception as e:
        print(f'Attempt {i+1}/{max_attempts}: Database not ready ({type(e).__name__}), waiting...')
        time.sleep(2)
else:
    print('Database failed to become ready after 60 seconds')
    exit(1)
"

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting FastAPI server on port $APP_PORT..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
