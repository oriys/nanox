# Nano E-commerce Platform

A comprehensive headless e-commerce platform built with Python microservices architecture, featuring gRPC communication, PostgreSQL/Redis data stores, and Kubernetes deployment.

## 🏗️ Architecture

### Core Services
- **User Service** (Port 50051/8001): User authentication and profile management
- **Product Service** (Port 50052/8002): Product catalog and inventory management
- **Cart Service** (Port 50053/8003): Shopping cart operations with Redis caching
- **Order Service** (Port 50054/8004): Order processing and management
- **Payment Service** (Port 50055/8005): Payment processing and transactions
- **Store Service** (Port 50056/8006): Multi-store management
- **API Gateway** (Port 8000): REST API gateway with gRPC backend communication

### Infrastructure
- **PostgreSQL**: Primary database for persistent data
- **Redis**: Caching layer for cart service and session management
- **gRPC**: Inter-service communication
- **Docker**: Containerization
- **Kubernetes**: Orchestration and deployment
- **Prometheus + Grafana**: Monitoring and metrics
- **Elasticsearch + Kibana**: Logging and log visualization

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Kubernetes cluster (optional)

### 1. Local Development with Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd nano-e-commerce

# Start all services with Docker Compose
./scripts/dev-start.sh

# Run database migrations
./scripts/migrate.sh

# Test the platform
./scripts/test-integration.sh
```

### 2. Local Development without Docker

```bash
# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Start services locally
./scripts/dev-start-local.sh

# Stop services
./scripts/dev-stop-local.sh
```

### 3. Kubernetes Deployment

```bash
# Build Docker images
./scripts/build-images.sh

# Deploy to Kubernetes (development)
./scripts/k8s-deploy.sh -e development

# Deploy to Kubernetes (production)
./scripts/k8s-deploy.sh -e production

# Port forward API Gateway for local access
kubectl port-forward -n nano-ecommerce service/api-gateway 8000:8000
```

## 🔧 Development

### Project Structure

```
nano-e-commerce/
├── services/                  # Microservices
│   ├── user-service/         # User management
│   ├── product-service/      # Product catalog
│   ├── cart-service/         # Shopping cart
│   ├── order-service/        # Order processing
│   ├── payment-service/      # Payment handling
│   ├── store-service/        # Store management
│   └── api-gateway/          # REST API gateway
├── shared/                   # Shared resources
│   ├── database/            # Database schemas and migrations
│   └── proto/               # Protocol buffer definitions
├── k8s/                     # Kubernetes manifests
│   ├── base/               # Base configurations
│   ├── development/        # Development environment
│   └── production/         # Production environment
├── scripts/                # Deployment and utility scripts
└── docker-compose.yml      # Docker Compose configuration
```

### Database Schema

The platform uses a comprehensive PostgreSQL schema with:
- UUID primary keys for better distribution
- Proper foreign key constraints
- Indexes for performance optimization
- Triggers for audit trails
- JSONB fields for flexible data storage

### Service Communication

Services communicate using:
- **gRPC**: For internal service-to-service communication
- **REST**: For external API access through the gateway
- **Protocol Buffers**: For message serialization

### API Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

#### Products
- `GET /products` - List all products
- `GET /products/{id}` - Get product details
- `POST /products` - Create product (admin)
- `PUT /products/{id}` - Update product (admin)
- `DELETE /products/{id}` - Delete product (admin)

#### Cart
- `GET /cart` - Get user's cart
- `POST /cart/items` - Add item to cart
- `PUT /cart/items/{id}` - Update cart item
- `DELETE /cart/items/{id}` - Remove cart item
- `DELETE /cart` - Clear cart

#### Orders
- `GET /orders` - Get user's orders
- `POST /orders` - Create order from cart
- `GET /orders/{id}` - Get order details
- `PUT /orders/{id}/status` - Update order status

#### Payments
- `GET /payments/methods` - Get payment methods
- `POST /payments` - Process payment
- `GET /payments/{id}` - Get payment details

#### Stores
- `GET /stores` - List all stores
- `GET /stores/{id}` - Get store details
- `POST /stores` - Create store (admin)
- `PUT /stores/{id}` - Update store (admin)

## 🔨 Scripts

### Build and Deployment
- `./scripts/build-images.sh` - Build all Docker images
- `./scripts/dev-start.sh` - Start development environment with Docker
- `./scripts/dev-start-local.sh` - Start services locally
- `./scripts/dev-stop-local.sh` - Stop local services
- `./scripts/k8s-deploy.sh` - Deploy to Kubernetes
- `./scripts/migrate.sh` - Run database migrations

### Testing
- `./scripts/test-basic.sh` - Basic infrastructure tests
- `./scripts/test-api.sh` - API endpoint tests
- `./scripts/test-integration.sh` - Comprehensive integration tests

## 🎯 Configuration

### Environment Variables

#### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

#### Service Configuration
- `ENVIRONMENT`: deployment environment (development/production)
- `DEBUG`: debug mode (true/false)
- `LOG_LEVEL`: logging level (DEBUG/INFO/WARNING/ERROR)

#### Authentication
- `JWT_SECRET`: JWT token secret
- `JWT_EXPIRATION`: Token expiration time

#### Service Discovery
- `USER_SERVICE_URL`: User service gRPC URL
- `PRODUCT_SERVICE_URL`: Product service gRPC URL
- `CART_SERVICE_URL`: Cart service gRPC URL
- `ORDER_SERVICE_URL`: Order service gRPC URL
- `PAYMENT_SERVICE_URL`: Payment service gRPC URL
- `STORE_SERVICE_URL`: Store service gRPC URL

## 📊 Monitoring

### Metrics Collection
- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics and creates dashboards
- Custom metrics for business logic

### Logging
- **Elasticsearch**: Stores and indexes logs
- **Kibana**: Log visualization and search
- Structured logging with correlation IDs

### Health Checks
- HTTP health endpoints for all services
- Kubernetes readiness and liveness probes
- Database connection monitoring

## 🚦 Testing

### Test Levels
1. **Unit Tests**: Individual service logic
2. **Integration Tests**: Service communication
3. **API Tests**: End-to-end API workflows
4. **Load Tests**: Performance and scalability

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Service-to-service authentication via mTLS (planned)

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- Rate limiting on API endpoints
- CORS configuration

## 🛠️ Development Workflow

### Local Development
1. Start infrastructure: `docker-compose up -d postgres redis`
2. Run migrations: `./scripts/migrate.sh`
3. Start services: `./scripts/dev-start-local.sh`
4. Run tests: `./scripts/test-integration.sh`

### Debugging
- Service logs: `docker-compose logs [service-name]`
- Database access: `docker exec -it nano-e-commerce-postgres-1 psql -U ecommerce_user -d ecommerce_db`
- Redis access: `docker exec -it nano-e-commerce-redis-1 redis-cli`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use type hints
- Write comprehensive tests
- Document APIs and functions
- Follow conventional commit messages

---

Built with ❤️ by the Nano E-commerce Team
