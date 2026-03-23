#!/bin/bash

echo "🚀 Starting Enrico Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
uv run python -c "
import time
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/enrico_cerrini_dev')
print(f'Connecting to: {db_url}')

# Parse database URL
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
        print('✅ Database connection successful!')
        break
    except Exception as e:
        print(f'⏳ Attempt {i+1}/{max_attempts}: Database not ready ({str(e)}), waiting...')
        time.sleep(2)
else:
    print('❌ Database failed to become ready after 60 seconds')
    exit(1)
"

# Run migrations
echo "📦 Running database migrations..."
uv run alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Start the server
echo "🌐 Starting FastAPI server..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
