#!/bin/bash

# OralSmart Docker Deployment Script
set -e

echo "Starting OralSmart deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Copying from .env.example"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your settings before continuing"
        read -p "Press Enter when ready to continue..."
    else
        print_error ".env.example file not found. Please create .env file manually."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p docker/ssl
mkdir -p logs
mkdir -p src/media
mkdir -p src/staticfiles

# Build and start services
print_status "Building Docker images..."
docker-compose build --no-cache

print_status "Starting services..."
docker-compose up -d

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 30

# Run migrations
print_status "Running database migrations..."
docker-compose exec web python manage.py migrate

# Create superuser if it doesn't exist
print_status "Checking for superuser..."
if [ -f "superuserDetails.txt" ]; then
    print_status "Creating superuser from superuserDetails.txt..."
    docker-compose exec web python manage.py shell < superuserDetails.txt || true
fi

# Load initial data if needed
if [ -f "src/fixtures/initial_data.json" ]; then
    print_status "Loading initial data..."
    docker-compose exec web python manage.py loaddata initial_data.json
fi

# Check service health
print_status "Checking service health..."
sleep 10

# Check if web service is healthy
if docker-compose ps web | grep -q "Up.*healthy"; then
    print_success "Web service is healthy"
else
    print_warning "Web service might not be fully ready yet"
fi

# Check if database is accessible
if docker-compose exec db mysqladmin ping -h localhost --silent; then
    print_success "Database is accessible"
else
    print_error "Database is not accessible"
fi

# Show running services
print_status "Current service status:"
docker-compose ps

# Show logs for any failed services
failed_services=$(docker-compose ps --filter "status=exited" --format "table {{.Service}}" | tail -n +2)
if [ ! -z "$failed_services" ]; then
    print_error "Some services failed to start:"
    echo "$failed_services"
    print_status "Showing logs for failed services:"
    for service in $failed_services; do
        print_status "Logs for $service:"
        docker-compose logs --tail=20 $service
    done
fi

print_success "Deployment completed!"
echo ""
print_status "Application URLs:"
echo "  Web Application: http://localhost:8000"
echo "  Admin Panel: http://localhost:8000/admin"
echo "  API Health Check: http://localhost:8000/health"
echo ""
print_status "Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Restart services: docker-compose restart"
echo "  Stop services: docker-compose down"
echo "  🧹 Clean up: docker-compose down -v --rmi all"
echo ""
print_status "For production deployment, use docker-compose-prod.yml"
