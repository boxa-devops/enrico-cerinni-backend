#!/bin/bash

echo "🧪 Testing Backend Setup..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start fresh
echo "🚀 Starting fresh containers..."
docker-compose up --build

echo "✅ Test complete!"
