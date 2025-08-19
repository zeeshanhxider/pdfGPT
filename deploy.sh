#!/bin/bash

# Production deployment script for PDF ChatBot RAG Application

set -e  # Exit on any error

echo "🚀 Starting PDF ChatBot RAG Application Deployment..."

# Configuration
DOMAIN=${1:-"localhost"}
ENV=${2:-"production"}
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo "📋 Deployment Configuration:"
echo "  Domain: $DOMAIN"
echo "  Environment: $ENV"
echo "  Backup Directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to backup data
backup_data() {
    if [ -d "./data" ]; then
        echo "💾 Backing up existing data..."
        cp -r ./data "$BACKUP_DIR/"
        echo "✅ Data backed up to $BACKUP_DIR"
    fi
}

# Function to setup environment files
setup_environment() {
    echo "🔧 Setting up environment files..."
    
    # Backend environment
    if [ ! -f "./backend/.env" ]; then
        cp ./backend/.env.example ./backend/.env
        
        # Update for production
        if [ "$ENV" = "production" ]; then
            sed -i "s/DEBUG=false/DEBUG=false/g" ./backend/.env
            sed -i "s/localhost/$DOMAIN/g" ./backend/.env
        fi
    fi
    
    # Frontend environment
    if [ ! -f "./frontend/.env.local" ]; then
        cp ./frontend/.env.local.example ./frontend/.env.local
        
        # Update API URL
        if [ "$DOMAIN" != "localhost" ]; then
            sed -i "s|http://localhost:8000|https://api.$DOMAIN|g" ./frontend/.env.local
        fi
    fi
    
    echo "✅ Environment files configured"
}

# Function to build and deploy
deploy() {
    echo "🏗️ Building and deploying services..."
    
    # Stop existing services
    docker-compose down || true
    
    # Remove old images (optional)
    read -p "Remove old Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down --rmi all
    fi
    
    # Build and start services
    if [ "$ENV" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    else
        docker-compose up -d --build
    fi
    
    echo "✅ Services deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    echo "🔍 Verifying deployment..."
    
    # Wait for services to start
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Check backend health
    echo "🔬 Checking backend health..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
    else
        echo "❌ Backend health check failed"
        exit 1
    fi
    
    # Check frontend
    echo "🔬 Checking frontend..."
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is accessible"
    else
        echo "❌ Frontend check failed"
        exit 1
    fi
    
    echo "✅ Deployment verification completed"
}

# Function to show deployment info
show_info() {
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Access Information:"
    echo "  Frontend:      http://$DOMAIN:3000"
    echo "  Backend API:   http://$DOMAIN:8000"
    echo "  API Docs:      http://$DOMAIN:8000/docs"
    echo "  Health Check:  http://$DOMAIN:8000/health"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:     docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart:       docker-compose restart"
    echo ""
    echo "💾 Backup Location: $BACKUP_DIR"
}

# Function to setup monitoring
setup_monitoring() {
    echo "📊 Setting up monitoring..."
    
    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash
# Simple monitoring script

check_service() {
    local service=$1
    local url=$2
    
    if curl -f "$url" > /dev/null 2>&1; then
        echo "✅ $service is healthy"
        return 0
    else
        echo "❌ $service is down"
        return 1
    fi
}

echo "🔍 Health Check Report - $(date)"
echo "================================"

check_service "Backend" "http://localhost:8000/health"
check_service "Frontend" "http://localhost:3000"

echo ""
echo "📊 Docker Status:"
docker-compose ps
EOF
    
    chmod +x monitor.sh
    echo "✅ Monitoring script created (./monitor.sh)"
}

# Main deployment flow
main() {
    # Backup existing data
    backup_data
    
    # Setup environment
    setup_environment
    
    # Deploy services
    deploy
    
    # Verify deployment
    verify_deployment
    
    # Setup monitoring
    setup_monitoring
    
    # Show deployment info
    show_info
}

# Run main function
main
