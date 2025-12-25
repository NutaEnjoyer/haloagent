#!/bin/bash
set -e

echo "🚀 Deploying Halo Voice Caller API..."

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

# Pull latest changes if git repo
if [ -d ".git" ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main || git pull origin master
fi

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services
echo "⏳ Waiting for services..."
sleep 15

# Check health
echo "🏥 Checking health..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f docker-compose.production.yml logs backend
    exit 1
fi

echo "✅ Deployment completed!"
echo ""
echo "Services:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:8012"
echo ""
echo "View logs:"
echo "  docker-compose -f docker-compose.production.yml logs -f"
