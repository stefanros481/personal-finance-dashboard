#!/bin/bash

# Personal Finance Dashboard Start Script

echo "🚀 Starting Personal Finance Dashboard..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Start services
echo "📦 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if backend is healthy
echo "🔍 Checking backend health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend is not responding. Check logs with: docker-compose logs backend"
    exit 1
fi

# Initialize database if needed
echo "🗄️  Initializing database..."
docker-compose exec -T backend python scripts/init_db.py

echo ""
echo "🎉 Personal Finance Dashboard is ready!"
echo ""
echo "📋 Available services:"
echo "   • API Documentation: http://localhost:8000/api/docs"
echo "   • API Health Check: http://localhost:8000/health"
echo "   • Database: PostgreSQL on localhost:5432"
echo "   • Cache: Redis on localhost:6379"
echo ""
echo "🔑 Test credentials:"
echo "   • Email: test@example.com"
echo "   • Password: testpass"
echo ""
echo "📝 Useful commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • View status: docker-compose ps"