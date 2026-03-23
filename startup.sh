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
print(f'Connecting to: {db_url}')

parts = db_url.replace('postgresql://', '').split('/')
db_name = parts[-1]
user_pass_host = parts[0]
user_pass, host_port = user_pass_host.split('@')
user, password = user_pass.split(':')
host, port = host_port.split(':')

max_attempts = 30
for i in range(max_attempts):
    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=db_name,
            user=user,
            password=password
        )
        conn.close()
        print('Database connection successful!')
        break
    except Exception as e:
        print(f'Attempt {i+1}/{max_attempts}: Database not ready ({str(e)}), waiting...')
        time.sleep(2)
else:
    print('Database failed to become ready after 60 seconds')
    exit(1)
"

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting FastAPI server on port $APP_PORT..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"
