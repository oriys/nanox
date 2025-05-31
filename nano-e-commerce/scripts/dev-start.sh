#!/bin/bash

echo "🚀 Starting Nano E-Commerce Platform Development Environment..."

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

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Change to project root
cd "$(dirname "$0")/.."

# Start infrastructure services (PostgreSQL, Redis)
print_info "Starting infrastructure services..."
docker-compose up -d postgres redis

# Wait for services to be ready
print_info "Waiting for infrastructure services to be ready..."
sleep 15

# Run database migrations
print_info "Running database migrations..."
./scripts/migrate.sh --with-sample-data

# Build and start all microservices
print_info "Building and starting all microservices..."
docker-compose up -d

# Wait for services to start
print_info "Waiting for all services to start..."
sleep 20

# Check service health
print_info "Checking service health..."
services=("user-service:50051" "product-service:50052" "cart-service:50053" "order-service:50054" "payment-service:50055" "store-service:50056" "api-gateway:8000")

all_healthy=true
for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if nc -z localhost $port 2>/dev/null; then
        print_success "$name is running on port $port"
    else
        print_error "$name is not responding on port $port"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    print_success "All services are running successfully!"
else
    print_warning "Some services may not be ready yet. Check logs with: docker-compose logs"
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
print_info "🧪 Test the API:"
echo "  ./scripts/test-api.sh"
echo ""
print_info "📊 View logs:"
echo "  docker-compose logs -f [service-name]"
echo ""
print_info "🛑 Stop services:"
echo "  docker-compose down"
