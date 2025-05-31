#!/bin/bash

# Docker image build script for nano-e-commerce platform
# Builds all microservice Docker images with error handling and logging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="nano-ecommerce"
BUILD_PARALLEL=false
PUSH_IMAGES=false
REGISTRY=""
TAG="latest"

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

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --parallel          Build images in parallel"
    echo "  --push                  Push images to registry after building"
    echo "  -r, --registry REGISTRY Registry URL for pushing images"
    echo "  -t, --tag TAG           Tag for images [default: latest]"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                  # Build all images sequentially"
    echo "  $0 --parallel                      # Build images in parallel"
    echo "  $0 --push -r my-registry.com       # Build and push to registry"
    echo "  $0 -t v1.0.0                       # Build with specific tag"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--parallel)
            BUILD_PARALLEL=true
            shift
            ;;
        --push)
            PUSH_IMAGES=true
            shift
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

print_header "Nano E-commerce Platform Docker Build"
print_status "Project: $PROJECT_NAME"
print_status "Tag: $TAG"
print_status "Parallel Build: $BUILD_PARALLEL"
print_status "Push Images: $PUSH_IMAGES"
if [[ -n "$REGISTRY" ]]; then
    print_status "Registry: $REGISTRY"
fi

# Define services to build
SERVICES=("user-service" "product-service" "cart-service" "order-service" "payment-service" "store-service" "api-gateway")
FAILED_BUILDS=()
SUCCESSFUL_BUILDS=()

# Function to build a single service
build_service() {
    local service="$1"
    local service_dir="services/$service"
    
    print_status "Building $service..."
    
    if [[ ! -d "$service_dir" ]]; then
        print_warning "$service directory not found, skipping"
        return 1
    fi
    
    if [[ ! -f "$service_dir/Dockerfile" ]]; then
        print_warning "$service Dockerfile not found, skipping"
        return 1
    fi
    
    # Construct image name
    local image_name="$PROJECT_NAME/$service:$TAG"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$PROJECT_NAME/$service:$TAG"
    fi
    
    # Build the image
    if docker build -t "$image_name" "$service_dir"; then
        print_status "✅ $service built successfully"
        SUCCESSFUL_BUILDS+=("$service")
        
        # Push if requested
        if [[ "$PUSH_IMAGES" == true ]]; then
            print_status "Pushing $service to registry..."
            if docker push "$image_name"; then
                print_status "✅ $service pushed successfully"
            else
                print_error "❌ Failed to push $service"
                return 1
            fi
        fi
        
        return 0
    else
        print_error "❌ Failed to build $service"
        FAILED_BUILDS+=("$service")
        return 1
    fi
}

# Build images
if [[ "$BUILD_PARALLEL" == true ]]; then
    print_header "Building Images in Parallel"
    
    # Build all services in parallel
    pids=()
    for service in "${SERVICES[@]}"; do
        build_service "$service" &
        pids+=($!)
    done
    
    # Wait for all builds to complete
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            print_warning "One or more parallel builds failed"
        fi
    done
else
    print_header "Building Images Sequentially"
    
    # Build services one by one
    for service in "${SERVICES[@]}"; do
        build_service "$service" || true
    done
fi

print_header "Build Summary"

# Show build results
if [[ ${#SUCCESSFUL_BUILDS[@]} -gt 0 ]]; then
    print_status "Successfully built services:"
    for service in "${SUCCESSFUL_BUILDS[@]}"; do
        echo -e "  ${GREEN}✅${NC} $service"
    done
fi

if [[ ${#FAILED_BUILDS[@]} -gt 0 ]]; then
    print_error "Failed to build services:"
    for service in "${FAILED_BUILDS[@]}"; do
        echo -e "  ${RED}❌${NC} $service"
    done
fi

# Show image list
print_header "Built Images"
docker images | grep "$PROJECT_NAME" || print_warning "No images found with project name: $PROJECT_NAME"

# Exit with error if any builds failed
if [[ ${#FAILED_BUILDS[@]} -gt 0 ]]; then
    print_error "Build completed with ${#FAILED_BUILDS[@]} failure(s)"
    exit 1
else
    print_status "All images built successfully! 🎉"
    exit 0
fi
