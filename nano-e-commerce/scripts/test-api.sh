#!/bin/bash

# API testing script for nano-e-commerce platform
set -e

# API Gateway URL
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to make HTTP requests and check responses
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    print_info "Testing: $description"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $TOKEN" \
            -d "$data" \
            "$API_BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Authorization: Bearer $TOKEN" \
            "$API_BASE_URL$endpoint")
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all lines except last)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        print_success "$method $endpoint - Status: $status_code"
        echo "Response: $response_body" | jq . 2>/dev/null || echo "Response: $response_body"
    else
        print_error "$method $endpoint - Expected: $expected_status, Got: $status_code"
        echo "Response: $response_body"
        return 1
    fi
    echo
}

# Test suite
run_tests() {
    print_info "🧪 Starting API Tests for Nano E-Commerce Platform"
    echo "API Base URL: $API_BASE_URL"
    echo

    # Test 1: Health checks
    print_info "=== HEALTH CHECKS ==="
    test_endpoint "GET" "/health" "" "200" "API Gateway Health Check"
    
    # Test 2: User registration and authentication
    print_info "=== USER AUTHENTICATION ==="
    
    # Register a new user
    USER_DATA='{
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }'
    test_endpoint "POST" "/auth/register" "$USER_DATA" "201" "User Registration"
    
    # Login user
    LOGIN_DATA='{
        "username": "testuser",
        "password": "testpassword123"
    }'
    
    print_info "Logging in user..."
    login_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$LOGIN_DATA" \
        "$API_BASE_URL/auth/login")
    
    # Extract token
    TOKEN=$(echo "$login_response" | jq -r '.access_token // .token // empty' 2>/dev/null)
    
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
        print_success "User login successful - Token obtained"
        echo "Token: ${TOKEN:0:20}..."
    else
        print_warning "Login may have issues, continuing without token"
        echo "Login response: $login_response"
        TOKEN=""
    fi
    echo

    # Test 3: Product operations
    print_info "=== PRODUCT OPERATIONS ==="
    test_endpoint "GET" "/products" "" "200" "Get All Products"
    test_endpoint "GET" "/products?category=Electronics" "" "200" "Get Products by Category"
    
    # Test 4: Cart operations (requires authentication)
    if [ -n "$TOKEN" ]; then
        print_info "=== CART OPERATIONS ==="
        test_endpoint "GET" "/cart" "" "200" "Get User Cart"
        
        # Add item to cart
        CART_ITEM='{
            "product_id": "00000000-0000-0000-0000-000000000001",
            "quantity": 2
        }'
        test_endpoint "POST" "/cart/items" "$CART_ITEM" "201" "Add Item to Cart"
        test_endpoint "GET" "/cart" "" "200" "Get Updated Cart"
    else
        print_warning "Skipping cart tests - no authentication token"
    fi

    # Test 5: Store operations
    print_info "=== STORE OPERATIONS ==="
    test_endpoint "GET" "/stores" "" "200" "Get All Stores"

    # Test 6: Order operations (requires authentication)
    if [ -n "$TOKEN" ]; then
        print_info "=== ORDER OPERATIONS ==="
        test_endpoint "GET" "/orders" "" "200" "Get User Orders"
        
        # Create order
        ORDER_DATA='{
            "items": [
                {
                    "product_id": "00000000-0000-0000-0000-000000000001",
                    "quantity": 1,
                    "price": 999.99
                }
            ],
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "country": "Test Country",
                "postal_code": "12345"
            }
        }'
        test_endpoint "POST" "/orders" "$ORDER_DATA" "201" "Create Order"
    else
        print_warning "Skipping order tests - no authentication token"
    fi

    print_info "🎉 API Testing Complete!"
    echo
    print_info "Next steps:"
    echo "  • Check individual service logs for details"
    echo "  • Monitor service performance"
    echo "  • Run integration tests"
}

# Check if API Gateway is running
check_api_gateway() {
    print_info "Checking if API Gateway is running..."
    
    if curl -s "$API_BASE_URL/health" > /dev/null 2>&1; then
        print_success "API Gateway is running at $API_BASE_URL"
    else
        print_error "API Gateway is not accessible at $API_BASE_URL"
        print_info "Please ensure services are running with: ./scripts/dev-start.sh"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed - JSON responses may not be formatted"
    fi
}

# Main execution
main() {
    echo "🧪 Nano E-Commerce API Test Suite"
    echo "=================================="
    
    check_dependencies
    check_api_gateway
    run_tests
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo ""
        echo "Environment Variables:"
        echo "  API_BASE_URL    API Gateway URL (default: http://localhost:8000)"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac