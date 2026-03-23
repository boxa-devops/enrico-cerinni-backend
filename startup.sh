#!/bin/bash
set -e

echo "Starting Enrico Backend..."

# Use Railway's PORT if available, fallback to 8000
APP_PORT=${PORT:-8000}

echo "Step 1: Checking Database Connection..."
uv run python -c "
import time
import psycopg2
import os
import sys

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/enrico_cerrini_dev')

if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

print(f'Attempting to connect to database (URL scheme normalized)...')

max_attempts = 30
for i in range(max_attempts):
    try:
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.close()
        print('✅ Database connection successful!')
        sys.exit(0)
    except Exception as e:
        print(f'⏳ Attempt {i+1}/{max_attempts}: Database not ready ({type(e).__name__}), retrying in 2s...')
        time.sleep(2)

print('❌ Database failed to become ready after 60 seconds')
sys.exit(1)
"

echo "Step 2: Running database migrations..."
if uv run alembic upgrade head; then
    echo "✅ Migrations completed successfully!"
else
    echo "⚠️ Migrations failed! Attempting to start the application anyway (might fail if schema is mismatched)..."
fi

echo "Step 3: Starting FastAPI server on port $APP_PORT..."
# Using --workers 1 to reduce memory footprint on startup in limited environments
exec uv run uvicorn main:app --host 0.0.0.0 --port "$APP_PORT" --proxy-headers --forwarded-allow-ips='*'
