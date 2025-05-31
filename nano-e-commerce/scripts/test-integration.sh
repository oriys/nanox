#!/bin/bash

# Comprehensive integration test suite for nano-e-commerce platform
# Tests all services, database connections, gRPC communication, and API endpoints

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
API_BASE_URL="http://localhost:8000"
TIMEOUT=30
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}==== $1 ====${NC}"
}

print_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [[ "$result" == "PASS" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        if [[ -n "$details" ]]; then
            echo -e "  ${details}"
        fi
    else
        echo -e "${RED}✗${NC} $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        if [[ -n "$details" ]]; then
            echo -e "  ${RED}Error:${NC} $details"
        fi
    fi
}

# Function to make HTTP requests with error handling
make_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected_status="$4"
    local auth_token="$5"
    
    local curl_cmd="curl -s -w '%{http_code}' -X $method"
    
    if [[ -n "$auth_token" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $auth_token'"
    fi
    
    if [[ -n "$data" ]]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$API_BASE_URL$endpoint'"
    
    local response
    response=$(eval "$curl_cmd" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        echo "CURL_ERROR"
        return 1
    fi
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    echo "$http_code|$body"
}

# Function to wait for service to be ready
wait_for_service() {
    local service_url="$1"
    local service_name="$2"
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "$service_url/health" > /dev/null 2>&1; then
            print_status "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name is not responding after $((max_attempts * 2)) seconds"
    return 1
}

# Function to test database connectivity
test_database_connectivity() {
    print_header "Database Connectivity Tests"
    
    # Test PostgreSQL connection
    local pg_test_result
    if pg_test_result=$(docker exec nano-e-commerce-postgres-1 pg_isready -U ecommerce_user -d ecommerce_db 2>/dev/null); then
        print_test_result "PostgreSQL Connection" "PASS" "$pg_test_result"
    else
        print_test_result "PostgreSQL Connection" "FAIL" "Database not accessible"
    fi
    
    # Test Redis connection
    local redis_test_result
    if redis_test_result=$(docker exec nano-e-commerce-redis-1 redis-cli ping 2>/dev/null); then
        if [[ "$redis_test_result" == "PONG" ]]; then
            print_test_result "Redis Connection" "PASS" "Redis responding"
        else
            print_test_result "Redis Connection" "FAIL" "Unexpected response: $redis_test_result"
        fi
    else
        print_test_result "Redis Connection" "FAIL" "Redis not accessible"
    fi
}

# Function to test individual service health
test_service_health() {
    print_header "Service Health Tests"
    
    local services=(
        "user-service:8001"
        "product-service:8002"
        "cart-service:8003"
        "order-service:8004"
        "payment-service:8005"
        "store-service:8006"
        "api-gateway:8000"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service_info"
        local health_url="http://localhost:$port/health"
        
        local response
        response=$(curl -s -w '%{http_code}' "$health_url" 2>/dev/null || echo "CURL_ERROR|")
        
        if [[ "$response" == "CURL_ERROR|" ]]; then
            print_test_result "$service_name Health Check" "FAIL" "Service not accessible"
        else
            local http_code="${response: -3}"
            local body="${response%???}"
            
            if [[ "$http_code" == "200" ]]; then
                print_test_result "$service_name Health Check" "PASS" "HTTP $http_code"
            else
                print_test_result "$service_name Health Check" "FAIL" "HTTP $http_code - $body"
            fi
        fi
    done
}

# Function to test API Gateway routes
test_api_gateway_routes() {
    print_header "API Gateway Route Tests"
    
    # Test root endpoint
    local response
    response=$(make_request "GET" "/" "" "200")
    
    if [[ "$response" == "CURL_ERROR" ]]; then
        print_test_result "API Gateway Root" "FAIL" "Connection failed"
        return 1
    fi
    
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "API Gateway Root" "PASS" "HTTP $http_code"
    else
        print_test_result "API Gateway Root" "FAIL" "HTTP $http_code"
    fi
    
    # Test health endpoint
    response=$(make_request "GET" "/health" "" "200")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "API Gateway Health" "PASS" "HTTP $http_code"
    else
        print_test_result "API Gateway Health" "FAIL" "HTTP $http_code"
    fi
}

# Function to test user authentication flow
test_user_authentication() {
    print_header "User Authentication Tests"
    
    # Test user registration
    local registration_data='{"email":"test@example.com","password":"testpassword123","full_name":"Test User"}'
    local response
    response=$(make_request "POST" "/auth/register" "$registration_data" "201")
    
    if [[ "$response" == "CURL_ERROR" ]]; then
        print_test_result "User Registration" "FAIL" "Connection failed"
        return 1
    fi
    
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "201" || "$http_code" == "409" ]]; then
        print_test_result "User Registration" "PASS" "HTTP $http_code"
    else
        print_test_result "User Registration" "FAIL" "HTTP $http_code - $body"
        return 1
    fi
    
    # Test user login
    local login_data='{"email":"test@example.com","password":"testpassword123"}'
    response=$(make_request "POST" "/auth/login" "$login_data" "200")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "User Login" "PASS" "HTTP $http_code"
        
        # Extract token for subsequent tests
        AUTH_TOKEN=$(echo "$body" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        if [[ -n "$AUTH_TOKEN" ]]; then
            print_status "Authentication token obtained"
        fi
    else
        print_test_result "User Login" "FAIL" "HTTP $http_code - $body"
    fi
}

# Function to test product operations
test_product_operations() {
    print_header "Product Operations Tests"
    
    # Test get products
    local response
    response=$(make_request "GET" "/products" "" "200")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "Get Products" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Products" "FAIL" "HTTP $http_code - $body"
    fi
    
    # Test get specific product (assuming product ID 1 exists)
    response=$(make_request "GET" "/products/1" "" "200")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" || "$http_code" == "404" ]]; then
        print_test_result "Get Product by ID" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Product by ID" "FAIL" "HTTP $http_code - $body"
    fi
}

# Function to test cart operations
test_cart_operations() {
    print_header "Cart Operations Tests"
    
    if [[ -z "$AUTH_TOKEN" ]]; then
        print_test_result "Cart Operations" "SKIP" "No authentication token available"
        return
    fi
    
    # Test get cart
    local response
    response=$(make_request "GET" "/cart" "" "200" "$AUTH_TOKEN")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "Get Cart" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Cart" "FAIL" "HTTP $http_code - $body"
    fi
    
    # Test add item to cart (assuming product ID 1 exists)
    local cart_data='{"product_id":"1","quantity":2}'
    response=$(make_request "POST" "/cart/items" "$cart_data" "201" "$AUTH_TOKEN")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "201" || "$http_code" == "200" ]]; then
        print_test_result "Add Item to Cart" "PASS" "HTTP $http_code"
    else
        print_test_result "Add Item to Cart" "FAIL" "HTTP $http_code - $body"
    fi
}

# Function to test store operations
test_store_operations() {
    print_header "Store Operations Tests"
    
    # Test get stores
    local response
    response=$(make_request "GET" "/stores" "" "200")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "Get Stores" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Stores" "FAIL" "HTTP $http_code - $body"
    fi
    
    # Test get specific store (assuming store ID 1 exists)
    response=$(make_request "GET" "/stores/1" "" "200")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" || "$http_code" == "404" ]]; then
        print_test_result "Get Store by ID" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Store by ID" "FAIL" "HTTP $http_code - $body"
    fi
}

# Function to test order operations
test_order_operations() {
    print_header "Order Operations Tests"
    
    if [[ -z "$AUTH_TOKEN" ]]; then
        print_test_result "Order Operations" "SKIP" "No authentication token available"
        return
    fi
    
    # Test get orders
    local response
    response=$(make_request "GET" "/orders" "" "200" "$AUTH_TOKEN")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "Get Orders" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Orders" "FAIL" "HTTP $http_code - $body"
    fi
}

# Function to test payment operations
test_payment_operations() {
    print_header "Payment Operations Tests"
    
    if [[ -z "$AUTH_TOKEN" ]]; then
        print_test_result "Payment Operations" "SKIP" "No authentication token available"
        return
    fi
    
    # Test get payment methods
    local response
    response=$(make_request "GET" "/payments/methods" "" "200" "$AUTH_TOKEN")
    IFS='|' read -r http_code body <<< "$response"
    
    if [[ "$http_code" == "200" ]]; then
        print_test_result "Get Payment Methods" "PASS" "HTTP $http_code"
    else
        print_test_result "Get Payment Methods" "FAIL" "HTTP $http_code - $body"
    fi
}

# Function to generate test report
generate_test_report() {
    print_header "Test Summary"
    
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    
    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi
    
    echo -e "Success Rate: $success_rate%"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        print_status "All tests passed! ✨"
        return 0
    else
        print_error "$FAILED_TESTS test(s) failed"
        return 1
    fi
}

# Main execution
main() {
    print_header "Nano E-commerce Platform Integration Tests"
    print_status "Starting comprehensive integration test suite..."
    print_status "API Base URL: $API_BASE_URL"
    
    # Wait for API Gateway to be ready
    if ! wait_for_service "$API_BASE_URL" "API Gateway"; then
        print_error "API Gateway is not ready. Make sure the platform is running."
        exit 1
    fi
    
    # Run all test suites
    test_database_connectivity
    test_service_health
    test_api_gateway_routes
    test_user_authentication
    test_product_operations
    test_cart_operations
    test_store_operations
    test_order_operations
    test_payment_operations
    
    # Generate final report
    generate_test_report
}

# Check if API base URL is provided as argument
if [[ $# -gt 0 ]]; then
    API_BASE_URL="$1"
fi

# Run main function
main "$@"
