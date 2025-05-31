#!/bin/bash

# Platform status check script for nano-e-commerce
# Provides a comprehensive overview of all components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8000"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}==== $1 ====${NC}"
}

print_section() {
    echo -e "${CYAN}--- $1 ---${NC}"
}

# Function to check if a service is running
check_service_health() {
    local service_name="$1"
    local health_url="$2"
    
    if curl -s -f "$health_url" > /dev/null 2>&1; then
        print_status "$service_name is running"
        return 0
    else
        print_error "$service_name is not responding"
        return 1
    fi
}

# Function to check Docker container status
check_docker_container() {
    local container_pattern="$1"
    local service_name="$2"
    
    local container_count
    container_count=$(docker ps --filter "name=$container_pattern" --format "table {{.Names}}" | grep -c "$container_pattern" || echo "0")
    
    if [[ "$container_count" -gt 0 ]]; then
        print_status "$service_name container(s) running ($container_count)"
        return 0
    else
        print_error "$service_name containers not found"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    print_section "Database Connectivity"
    
    # PostgreSQL check
    if docker exec nano-e-commerce-postgres-1 pg_isready -U ecommerce_user -d ecommerce_db > /dev/null 2>&1; then
        print_status "PostgreSQL is accessible"
        
        # Check table count
        local table_count
        table_count=$(docker exec nano-e-commerce-postgres-1 psql -U ecommerce_user -d ecommerce_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
        print_info "PostgreSQL has $table_count tables"
    else
        print_error "PostgreSQL is not accessible"
    fi
    
    # Redis check
    if docker exec nano-e-commerce-redis-1 redis-cli ping > /dev/null 2>&1; then
        print_status "Redis is accessible"
        
        # Check Redis info
        local redis_info
        redis_info=$(docker exec nano-e-commerce-redis-1 redis-cli info server | grep "redis_version" | cut -d: -f2 | tr -d '\r')
        print_info "Redis version: $redis_info"
    else
        print_error "Redis is not accessible"
    fi
}

# Function to check microservices
check_microservices() {
    print_section "Microservices Status"
    
    local services=(
        "user-service:8001"
        "product-service:8002"
        "cart-service:8003"
        "order-service:8004"
        "payment-service:8005"
        "store-service:8006"
        "api-gateway:8000"
    )
    
    local healthy_services=0
    local total_services=${#services[@]}
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service_info"
        local health_url="http://localhost:$port/health"
        
        if check_service_health "$service_name" "$health_url"; then
            ((healthy_services++))
        fi
    done
    
    print_info "Healthy services: $healthy_services/$total_services"
}

# Function to check Docker containers
check_docker_containers() {
    print_section "Docker Containers"
    
    local containers=(
        "nano-e-commerce-postgres:PostgreSQL Database"
        "nano-e-commerce-redis:Redis Cache"
        "nano-e-commerce-user-service:User Service"
        "nano-e-commerce-product-service:Product Service"
        "nano-e-commerce-cart-service:Cart Service"
        "nano-e-commerce-order-service:Order Service"
        "nano-e-commerce-payment-service:Payment Service"
        "nano-e-commerce-store-service:Store Service"
        "nano-e-commerce-api-gateway:API Gateway"
    )
    
    local running_containers=0
    local total_containers=${#containers[@]}
    
    for container_info in "${containers[@]}"; do
        IFS=':' read -r container_name service_name <<< "$container_info"
        
        if check_docker_container "$container_name" "$service_name"; then
            ((running_containers++))
        fi
    done
    
    print_info "Running containers: $running_containers/$total_containers"
}

# Function to check API Gateway
check_api_gateway() {
    print_section "API Gateway"
    
    if curl -s -f "$API_BASE_URL/health" > /dev/null 2>&1; then
        print_status "API Gateway is accessible"
        
        # Test a few endpoints
        local endpoints=(
            "/health:Health Check"
            "/docs:API Documentation"
            "/products:Products Endpoint"
        )
        
        for endpoint_info in "${endpoints[@]}"; do
            IFS=':' read -r endpoint description <<< "$endpoint_info"
            local response_code
            response_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL$endpoint" 2>/dev/null || echo "000")
            
            if [[ "$response_code" == "200" || "$response_code" == "401" ]]; then
                print_status "$description ($endpoint) - HTTP $response_code"
            else
                print_warning "$description ($endpoint) - HTTP $response_code"
            fi
        done
    else
        print_error "API Gateway is not accessible at $API_BASE_URL"
    fi
}

# Function to check system resources
check_system_resources() {
    print_section "System Resources"
    
    # Docker stats
    if command -v docker &> /dev/null; then
        print_info "Docker resource usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10
    fi
    
    # Disk usage
    print_info "Disk usage for project directory:"
    du -sh . 2>/dev/null || print_warning "Could not check disk usage"
}

# Function to check network connectivity
check_network() {
    print_section "Network Connectivity"
    
    # Check if ports are listening
    local ports=(5432 6379 8000 8001 8002 8003 8004 8005 8006)
    local listening_ports=0
    
    for port in "${ports[@]}"; do
        if command -v lsof &> /dev/null; then
            if lsof -i ":$port" > /dev/null 2>&1; then
                print_status "Port $port is listening"
                ((listening_ports++))
            else
                print_warning "Port $port is not listening"
            fi
        elif command -v netstat &> /dev/null; then
            if netstat -ln | grep ":$port " > /dev/null 2>&1; then
                print_status "Port $port is listening"
                ((listening_ports++))
            else
                print_warning "Port $port is not listening"
            fi
        fi
    done
    
    print_info "Listening ports: $listening_ports/${#ports[@]}"
}

# Function to check file structure
check_file_structure() {
    print_section "Project Structure"
    
    local required_dirs=(
        "services"
        "shared"
        "scripts"
        "k8s"
    )
    
    local required_files=(
        "docker-compose.yml"
        "README.md"
        "scripts/dev-start.sh"
        "scripts/build-images.sh"
        "scripts/k8s-deploy.sh"
        "scripts/test-integration.sh"
    )
    
    # Check directories
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            print_status "Directory '$dir' exists"
        else
            print_error "Directory '$dir' missing"
        fi
    done
    
    # Check files
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_status "File '$file' exists"
        else
            print_error "File '$file' missing"
        fi
    done
}

# Function to show deployment information
show_deployment_info() {
    print_section "Deployment Information"
    
    # Current environment detection
    if docker-compose ps > /dev/null 2>&1; then
        print_status "Docker Compose deployment detected"
        print_info "Services defined in docker-compose.yml:"
        docker-compose config --services | sed 's/^/  - /'
    fi
    
    # Kubernetes check
    if command -v kubectl &> /dev/null; then
        if kubectl config current-context > /dev/null 2>&1; then
            local current_context
            current_context=$(kubectl config current-context)
            print_info "Kubernetes context: $current_context"
            
            # Check if namespace exists
            if kubectl get namespace nano-ecommerce > /dev/null 2>&1; then
                print_status "Kubernetes namespace 'nano-ecommerce' exists"
                
                local pod_count
                pod_count=$(kubectl get pods -n nano-ecommerce --no-headers 2>/dev/null | wc -l | xargs)
                print_info "Pods in namespace: $pod_count"
            else
                print_warning "Kubernetes namespace 'nano-ecommerce' not found"
            fi
        else
            print_warning "Kubernetes not configured or not accessible"
        fi
    else
        print_info "kubectl not installed"
    fi
}

# Function to show summary
show_summary() {
    print_header "Platform Summary"
    
    echo -e "${CYAN}Nano E-commerce Platform Status Report${NC}"
    echo -e "Generated: $(date)"
    echo ""
    
    # Overall health assessment
    local health_score=0
    local max_score=10
    
    # Check basic components
    if docker ps --filter "name=nano-e-commerce-postgres" --format "table {{.Names}}" | grep -q postgres; then
        ((health_score++))
    fi
    
    if docker ps --filter "name=nano-e-commerce-redis" --format "table {{.Names}}" | grep -q redis; then
        ((health_score++))
    fi
    
    if curl -s -f "$API_BASE_URL/health" > /dev/null 2>&1; then
        health_score=$((health_score + 3))
    fi
    
    # Check services
    local services=("8001" "8002" "8003" "8004" "8005" "8006")
    for port in "${services[@]}"; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            ((health_score++))
        fi
    done
    
    # Calculate health percentage
    local health_percentage=$((health_score * 100 / max_score))
    
    if [[ $health_percentage -ge 80 ]]; then
        echo -e "${GREEN}✓ Platform Health: $health_percentage% (Excellent)${NC}"
    elif [[ $health_percentage -ge 60 ]]; then
        echo -e "${YELLOW}! Platform Health: $health_percentage% (Good)${NC}"
    elif [[ $health_percentage -ge 40 ]]; then
        echo -e "${YELLOW}! Platform Health: $health_percentage% (Fair)${NC}"
    else
        echo -e "${RED}✗ Platform Health: $health_percentage% (Poor)${NC}"
    fi
    
    echo ""
    print_info "Access the platform:"
    print_info "  • API Gateway: $API_BASE_URL"
    print_info "  • API Documentation: $API_BASE_URL/docs"
    print_info "  • Health Check: $API_BASE_URL/health"
    echo ""
    
    print_info "Useful commands:"
    print_info "  • View logs: docker-compose logs [service-name]"
    print_info "  • Restart services: docker-compose restart"
    print_info "  • Run tests: ./scripts/test-integration.sh"
    print_info "  • Deploy to K8s: ./scripts/k8s-deploy.sh"
}

# Main execution
main() {
    print_header "Nano E-commerce Platform Status Check"
    
    # Run all checks
    check_file_structure
    check_docker_containers
    check_database
    check_microservices
    check_api_gateway
    check_network
    check_system_resources
    show_deployment_info
    
    echo ""
    show_summary
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_BASE_URL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --api-url URL    API Gateway URL (default: http://localhost:8000)"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
