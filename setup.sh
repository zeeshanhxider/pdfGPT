#!/bin/bash

# Quick setup script for PDF ChatBot RAG Application

echo "🚀 PDF ChatBot RAG - Quick Setup"
echo "================================="

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}

# Setup environment files
setup_env() {
    echo "🔧 Setting up environment files..."
    
    # Backend environment
    if [ ! -f "./backend/.env" ]; then
        cp ./backend/.env.example ./backend/.env
        echo "✅ Backend .env file created"
    fi
    
    # Frontend environment
    if [ ! -f "./frontend/.env.local" ]; then
        cp ./frontend/.env.local.example ./frontend/.env.local
        echo "✅ Frontend .env.local file created"
    fi
}

# Quick start
quick_start() {
    echo "🏗️ Building and starting services..."
    
    # Pull base images first
    echo "📥 Pulling base images..."
    docker pull python:3.11-slim
    docker pull node:18-alpine
    
    # Build and start
    docker-compose up --build -d
    
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Check if services are running
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is running"
    else
        echo "⚠️ Backend might still be starting..."
    fi
    
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is running"
    else
        echo "⚠️ Frontend might still be starting..."
    fi
}

# Show access info
show_info() {
    echo ""
    echo "🎉 Setup completed!"
    echo ""
    echo "📋 Access your application:"
    echo "  🌐 Frontend:      http://localhost:3000"
    echo "  🔌 Backend API:   http://localhost:8000"
    echo "  📚 API Docs:      http://localhost:8000/docs"
    echo "  ❤️ Health Check:  http://localhost:8000/health"
    echo ""
    echo "🔧 Useful commands:"
    echo "  📊 View logs:     docker-compose logs -f"
    echo "  🛑 Stop:          docker-compose down"
    echo "  🔄 Restart:       docker-compose restart"
    echo ""
    echo "📖 Next steps:"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Upload a PDF document"
    echo "  3. Start asking questions!"
}

# Main execution
main() {
    check_prerequisites
    setup_env
    quick_start
    show_info
}

# Run if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
