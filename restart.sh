#!/bin/bash
# Simple restart script

echo "🔄 Restarting services..."
docker-compose -f docker-compose.production.yml restart

echo "⏳ Waiting for startup..."
sleep 10

echo "✅ Services restarted!"
echo "View logs: docker-compose -f docker-compose.production.yml logs -f"
