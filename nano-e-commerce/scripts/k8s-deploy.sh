#!/bin/bash

# Kubernetes deployment script for nano-e-commerce platform
# This script handles deployment to different environments (dev/prod)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
NAMESPACE="nano-ecommerce"
BUILD_IMAGES=true
APPLY_MANIFESTS=true

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
    echo "  -e, --environment ENV    Target environment (development|production) [default: development]"
    echo "  -n, --namespace NAME     Kubernetes namespace [default: nano-ecommerce]"
    echo "  --skip-build            Skip building Docker images"
    echo "  --skip-apply            Skip applying Kubernetes manifests"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Deploy to development"
    echo "  $0 -e production                           # Deploy to production"
    echo "  $0 --skip-build                           # Deploy without rebuilding images"
    echo "  $0 -e production -n my-namespace          # Deploy to production with custom namespace"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --skip-build)
            BUILD_IMAGES=false
            shift
            ;;
        --skip-apply)
            APPLY_MANIFESTS=false
            shift
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

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'development' or 'production'"
    exit 1
fi

print_header "Nano E-commerce Platform Kubernetes Deployment"
print_status "Environment: $ENVIRONMENT"
print_status "Namespace: $NAMESPACE"
print_status "Build Images: $BUILD_IMAGES"
print_status "Apply Manifests: $APPLY_MANIFESTS"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if kustomize is available
if ! command -v kustomize &> /dev/null; then
    print_error "kustomize is not installed or not in PATH"
    print_status "You can install it with: curl -s https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh | bash"
    exit 1
fi

# Check if Docker is available (if building images)
if [[ "$BUILD_IMAGES" == true ]] && ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check kubectl connection
print_status "Checking Kubernetes cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig"
    exit 1
fi

print_status "Connected to Kubernetes cluster: $(kubectl config current-context)"

# Build Docker images if requested
if [[ "$BUILD_IMAGES" == true ]]; then
    print_header "Building Docker Images"
    
    if [[ -f "./scripts/build-images.sh" ]]; then
        print_status "Running build script..."
        chmod +x ./scripts/build-images.sh
        ./scripts/build-images.sh
    else
        print_status "Building images manually..."
        
        # Build all service images
        services=("user-service" "product-service" "cart-service" "order-service" "payment-service" "store-service" "api-gateway")
        
        for service in "${services[@]}"; do
            if [[ -d "./services/$service" ]]; then
                print_status "Building $service..."
                docker build -t "nano-ecommerce/$service:latest" "./services/$service"
            else
                print_warning "Service directory not found: ./services/$service"
            fi
        done
    fi
    
    print_status "Docker images built successfully"
fi

# Apply Kubernetes manifests if requested
if [[ "$APPLY_MANIFESTS" == true ]]; then
    print_header "Deploying to Kubernetes"
    
    # Create namespace if it doesn't exist
    print_status "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests using kustomize
    print_status "Applying Kubernetes manifests for $ENVIRONMENT environment..."
    
    if [[ -d "./k8s/$ENVIRONMENT" ]]; then
        kustomize build "./k8s/$ENVIRONMENT" | kubectl apply -f -
    else
        print_error "Environment directory not found: ./k8s/$ENVIRONMENT"
        exit 1
    fi
    
    print_status "Kubernetes manifests applied successfully"
    
    # Wait for deployments to be ready
    print_header "Waiting for Deployments"
    
    print_status "Waiting for database services to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s
    
    print_status "Waiting for microservices to be ready..."
    services=("user-service" "product-service" "cart-service" "order-service" "payment-service" "store-service" "api-gateway")
    
    for service in "${services[@]}"; do
        print_status "Waiting for $service..."
        if [[ "$ENVIRONMENT" == "development" ]]; then
            kubectl wait --for=condition=ready pod -l app="dev-$service" -n "$NAMESPACE" --timeout=300s || true
        else
            kubectl wait --for=condition=ready pod -l app="prod-$service" -n "$NAMESPACE" --timeout=300s || true
        fi
    done
fi

print_header "Deployment Status"

# Show deployment status
print_status "Getting deployment status..."
kubectl get deployments -n "$NAMESPACE"

print_status "Getting service status..."
kubectl get services -n "$NAMESPACE"

print_status "Getting pod status..."
kubectl get pods -n "$NAMESPACE"

# Show ingress information if available
if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
    print_status "Getting ingress status..."
    kubectl get ingress -n "$NAMESPACE"
fi

print_header "Deployment Complete"

print_status "Nano E-commerce platform deployed successfully to $ENVIRONMENT environment!"
print_status "Namespace: $NAMESPACE"

# Show connection information
if [[ "$ENVIRONMENT" == "development" ]]; then
    print_status "For local development, you can port-forward the API gateway:"
    print_status "kubectl port-forward -n $NAMESPACE service/dev-api-gateway 8000:8000"
    print_status "Then access the API at: http://localhost:8000"
else
    print_status "For production access, configure your ingress controller and DNS"
    print_status "API will be available at: http://api.nano-ecommerce.local"
fi

print_status "To view logs: kubectl logs -f deployment/[service-name] -n $NAMESPACE"
print_status "To scale services: kubectl scale deployment [service-name] --replicas=N -n $NAMESPACE"
