#!/bin/bash

# Local development startup script for nano-e-commerce platform
# This script runs services locally without Docker for development

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Change to project root
cd "$(dirname "$0")/.."

print_info "🚀 Starting Nano E-Commerce Platform in Local Development Mode"

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check PostgreSQL installation
if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL client not found. Please install PostgreSQL."
    print_info "You can install it via: brew install postgresql"
fi

# Check Redis installation  
if ! command -v redis-cli &> /dev/null; then
    print_warning "Redis client not found. Please install Redis."
    print_info "You can install it via: brew install redis"
fi

# Start infrastructure services with Docker (lightweight)
print_info "Starting infrastructure services (PostgreSQL & Redis)..."
if docker-compose up -d postgres redis 2>/dev/null; then
    print_success "Infrastructure services started successfully"
else
    print_warning "Failed to start with Docker, trying local services..."
    
    # Try to start local PostgreSQL if available
    if command -v brew &> /dev/null; then
        brew services start postgresql 2>/dev/null || true
        brew services start redis 2>/dev/null || true
    fi
fi

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 5

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce"
export REDIS_URL="redis://localhost:6379"

# Function to setup service environment
setup_service() {
    local service_name=$1
    local service_path="services/$service_name"
    
    print_info "Setting up $service_name..."
    
    cd "$service_path"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment for $service_name"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        print_info "Installing dependencies for $service_name"
        pip install -q -r requirements.txt
    fi
    
    cd ../..
}

# Function to run service in background
run_service() {
    local service_name=$1
    local service_path="services/$service_name"
    local port=$2
    
    print_info "Starting $service_name on port $port..."
    
    cd "$service_path"
    source venv/bin/activate
    
    # Start the service in background
    nohup python main.py > "../logs/$service_name.log" 2>&1 &
    local pid=$!
    echo "$pid" > "../logs/$service_name.pid"
    
    cd ../..
    
    print_success "$service_name started with PID $pid"
}

# Create logs directory
mkdir -p services/logs

# Run database migrations
print_info "Running database migrations..."
if ./scripts/migrate.sh --with-sample-data; then
    print_success "Database migrations completed"
else
    print_warning "Database migrations may have issues, continuing..."
fi

# Setup all services
print_info "Setting up all microservices..."
services=("user-service" "product-service" "cart-service" "order-service" "payment-service" "store-service" "api-gateway")

for service in "${services[@]}"; do
    setup_service "$service"
done

# Start all services
print_info "Starting all microservices..."
run_service "user-service" "50051"
sleep 2
run_service "product-service" "50052"
sleep 2
run_service "cart-service" "50053"
sleep 2
run_service "order-service" "50054"
sleep 2
run_service "payment-service" "50055"
sleep 2
run_service "store-service" "50056"
sleep 2
run_service "api-gateway" "8000"

# Wait for all services to start
print_info "Waiting for all services to start..."
sleep 15

# Check service health
print_info "Checking service health..."
services_ports=("user-service:50051" "product-service:50052" "cart-service:50053" "order-service:50054" "payment-service:50055" "store-service:50056" "api-gateway:8000")

all_healthy=true
for service_port in "${services_ports[@]}"; do
    service=$(echo $service_port | cut -d: -f1)
    port=$(echo $service_port | cut -d: -f2)
    
    if nc -z localhost $port 2>/dev/null; then
        print_success "$service is running on port $port"
    else
        print_error "$service is not responding on port $port"
        print_info "Check logs: tail -f services/logs/$service.log"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    print_success "🎉 All services are running successfully!"
else
    print_warning "Some services may not be ready yet. Check individual service logs."
fi

echo ""
print_info "🌐 Service Endpoints:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - User Service (gRPC): localhost:50051"
echo "  - Product Service (gRPC): localhost:50052"
echo "  - Cart Service (gRPC): localhost:50053"
echo "  - Order Service (gRPC): localhost:50054"
echo "  - Payment Service (gRPC): localhost:50055"
echo "  - Store Service (gRPC): localhost:50056"
echo "  - API Gateway (HTTP): localhost:8000"
echo ""
print_info "📊 View logs:"
echo "  tail -f services/logs/[service-name].log"
echo ""
print_info "🧪 Test the API:"
echo "  ./scripts/test-api.sh"
echo ""
print_info "🛑 Stop all services:"
echo "  ./scripts/dev-stop-local.sh"