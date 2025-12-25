#!/bin/bash
# Simple stop script

echo "⏹️  Stopping services..."
docker-compose -f docker-compose.production.yml down

echo "✅ Services stopped!"
