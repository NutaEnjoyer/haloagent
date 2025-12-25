#!/bin/bash
# Simple start script

echo "🚀 Starting services..."
docker-compose -f docker-compose.production.yml up -d

echo "⏳ Waiting for startup..."
sleep 10

echo "✅ Services started!"
echo "View logs: docker-compose -f docker-compose.production.yml logs -f"
