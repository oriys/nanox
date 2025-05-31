#!/bin/bash

# Local development stop script for nano-e-commerce platform
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

print_info "🛑 Stopping Nano E-Commerce Platform Local Development Services"

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="services/logs/$service_name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_info "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            
            # Wait for process to stop
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Force killing $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            print_success "$service_name stopped"
        else
            print_info "$service_name was not running"
        fi
        rm -f "$pid_file"
    else
        print_info "No PID file found for $service_name"
    fi
}

# Stop all services
services=("api-gateway" "store-service" "payment-service" "order-service" "cart-service" "product-service" "user-service")

print_info "Stopping all microservices..."
for service in "${services[@]}"; do
    stop_service "$service"
done

# Kill any remaining Python processes that might be our services
print_info "Cleaning up any remaining service processes..."
pkill -f "main.py" 2>/dev/null || true

# Stop Docker services if they were started
print_info "Stopping infrastructure services..."
docker-compose down 2>/dev/null || true

# Stop local services if they were started
if command -v brew &> /dev/null; then
    brew services stop postgresql 2>/dev/null || true
    brew services stop redis 2>/dev/null || true
fi

# Clean up log files (optional)
if [ "$1" = "--clean-logs" ]; then
    print_info "Cleaning up log files..."
    rm -rf services/logs/*.log
    rm -rf services/logs/*.pid
fi

print_success "🎉 All services stopped successfully!"

print_info "💡 Useful commands:"
echo "  - Start services again: ./scripts/dev-start-local.sh"
echo "  - Start with Docker: ./scripts/dev-start.sh"
echo "  - Clean logs: ./scripts/dev-stop-local.sh --clean-logs"