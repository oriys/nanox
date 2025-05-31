#!/bin/bash

# Basic integration test for nano-e-commerce platform
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

print_info "🧪 Starting Basic Integration Tests for Nano E-Commerce Platform"

# Test 1: Check if PostgreSQL is accessible
test_postgres() {
    print_info "Testing PostgreSQL connection..."
    if PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d ecommerce -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "PostgreSQL is accessible"
        return 0
    else
        print_error "PostgreSQL connection failed"
        return 1
    fi
}

# Test 2: Check if Redis is accessible
test_redis() {
    print_info "Testing Redis connection..."
    if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        print_success "Redis is accessible"
        return 0
    else
        print_error "Redis connection failed"
        return 1
    fi
}

# Test 3: Check if services are listening on their ports
test_service_ports() {
    print_info "Testing service ports..."
    local all_ports_open=true
    
    ports=("50051:User Service" "50052:Product Service" "50053:Cart Service" "50054:Order Service" "50055:Payment Service" "50056:Store Service" "8000:API Gateway")
    
    for port_service in "${ports[@]}"; do
        port=$(echo $port_service | cut -d: -f1)
        service=$(echo $port_service | cut -d: -f2)
        
        if nc -z localhost $port 2>/dev/null; then
            print_success "$service is listening on port $port"
        else
            print_error "$service is NOT listening on port $port"
            all_ports_open=false
        fi
    done
    
    return $all_ports_open
}

# Test 4: Basic API Gateway health check
test_api_gateway() {
    print_info "Testing API Gateway health..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        print_success "API Gateway health check passed"
        return 0
    else
        print_error "API Gateway health check failed (HTTP $response)"
        return 1
    fi
}

# Test 5: Database schema verification
test_database_schema() {
    print_info "Testing database schema..."
    
    # Check if main tables exist
    tables=("users" "products" "cart_items" "orders" "payments" "stores")
    all_tables_exist=true
    
    for table in "${tables[@]}"; do
        if PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d ecommerce -c "\dt $table" | grep -q "$table"; then
            print_success "Table '$table' exists"
        else
            print_error "Table '$table' does not exist"
            all_tables_exist=false
        fi
    done
    
    return $all_tables_exist
}

# Test 6: Basic API endpoint tests
test_api_endpoints() {
    print_info "Testing basic API endpoints..."
    
    # Test product list endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/products 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        print_success "GET /products endpoint works"
    else
        print_error "GET /products endpoint failed (HTTP $response)"
        return 1
    fi
    
    # Test stores endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/stores 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        print_success "GET /stores endpoint works"
    else
        print_error "GET /stores endpoint failed (HTTP $response)"
        return 1
    fi
    
    return 0
}

# Main test execution
main() {
    local failed_tests=0
    
    print_info "🔍 Running Infrastructure Tests..."
    test_postgres || ((failed_tests++))
    test_redis || ((failed_tests++))
    
    print_info "🔍 Running Service Tests..."
    test_service_ports || ((failed_tests++))
    test_api_gateway || ((failed_tests++))
    
    print_info "🔍 Running Database Tests..."
    test_database_schema || ((failed_tests++))
    
    print_info "🔍 Running API Tests..."
    test_api_endpoints || ((failed_tests++))
    
    echo ""
    if [ $failed_tests -eq 0 ]; then
        print_success "🎉 All basic integration tests passed!"
        echo ""
        print_info "✨ Your nano-e-commerce platform is ready!"
        print_info "🌐 API Gateway: http://localhost:8000"
        print_info "📚 API Documentation: http://localhost:8000/docs"
        print_info "🧪 Run full API tests: ./scripts/test-api.sh"
    else
        print_error "❌ $failed_tests test(s) failed"
        echo ""
        print_info "🔧 Troubleshooting:"
        echo "  - Check if all services are running: ./scripts/dev-start-local.sh"
        echo "  - View service logs: tail -f services/logs/[service-name].log"
        echo "  - Restart infrastructure: docker-compose restart postgres redis"
        exit 1
    fi
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo ""
        echo "Basic integration test suite for nano-e-commerce platform"
        echo ""
        echo "Tests:"
        echo "  - Infrastructure connectivity (PostgreSQL, Redis)"
        echo "  - Service port availability"
        echo "  - API Gateway health"
        echo "  - Database schema"
        echo "  - Basic API endpoints"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac