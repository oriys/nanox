#!/bin/bash

# Database migration script for nano-e-commerce platform
set -e

echo "🚀 Starting database migration..."

# Default values
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ecommerce}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    print_status "Waiting for PostgreSQL to be ready..."
    until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c '\q' 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    print_status "PostgreSQL is ready!"
}

# Run database initialization
run_init() {
    print_status "Running database initialization..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -f shared/database/init.sql
    print_status "Database initialization completed!"
}

# Run migrations
run_migrations() {
    print_status "Running database migrations..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f shared/database/migrations.sql
    print_status "Database migrations completed!"
}

# Insert sample data
insert_sample_data() {
    print_status "Inserting sample data..."
    
    # Sample users
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
-- Insert sample users
INSERT INTO users (username, email, password_hash, full_name, phone, is_verified) VALUES 
('admin', 'admin@nano.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/SJQeUZ5Ue', 'Admin User', '+1234567890', true),
('john_doe', 'john@example.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/SJQeUZ5Ue', 'John Doe', '+1234567891', true),
('jane_smith', 'jane@example.com', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/SJQeUZ5Ue', 'Jane Smith', '+1234567892', true)
ON CONFLICT (email) DO NOTHING;

-- Insert sample stores
INSERT INTO stores (name, description, owner_id) VALUES 
('Tech Store', 'Electronics and gadgets store', (SELECT id FROM users WHERE username = 'admin')),
('Fashion Hub', 'Trendy clothing and accessories', (SELECT id FROM users WHERE username = 'john_doe')),
('Book Corner', 'Books and educational materials', (SELECT id FROM users WHERE username = 'jane_smith'))
ON CONFLICT DO NOTHING;

-- Insert sample products
INSERT INTO products (name, description, price, stock_quantity, category, store_id, sku) VALUES 
('iPhone 15', 'Latest Apple smartphone', 999.99, 50, 'Electronics', (SELECT id FROM stores WHERE name = 'Tech Store'), 'IP15-001'),
('MacBook Pro', 'Apple laptop for professionals', 1999.99, 25, 'Electronics', (SELECT id FROM stores WHERE name = 'Tech Store'), 'MBP-001'),
('Wireless Earbuds', 'High-quality bluetooth earbuds', 199.99, 100, 'Electronics', (SELECT id FROM stores WHERE name = 'Tech Store'), 'WE-001'),
('Designer T-Shirt', 'Premium cotton t-shirt', 49.99, 200, 'Clothing', (SELECT id FROM stores WHERE name = 'Fashion Hub'), 'TS-001'),
('Jeans', 'Classic blue jeans', 79.99, 150, 'Clothing', (SELECT id FROM stores WHERE name = 'Fashion Hub'), 'JN-001'),
('Programming Book', 'Learn Python programming', 39.99, 75, 'Books', (SELECT id FROM stores WHERE name = 'Book Corner'), 'PB-001')
ON CONFLICT (sku) DO NOTHING;
EOF

    print_status "Sample data inserted successfully!"
}

# Main execution
main() {
    print_status "Starting nano-e-commerce database migration"
    
    # Change to project root directory
    cd "$(dirname "$0")/.."
    
    # Wait for database to be ready
    wait_for_postgres
    
    # Run initialization
    run_init
    
    # Run migrations
    run_migrations
    
    # Insert sample data if requested
    if [[ "$1" == "--with-sample-data" ]]; then
        insert_sample_data
    fi
    
    print_status "✅ Database migration completed successfully!"
    print_warning "Next steps:"
    echo "  1. Start the services: ./scripts/dev-start.sh"
    echo "  2. Test the API: ./scripts/test-api.sh"
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [--with-sample-data] [--help]"
        echo ""
        echo "Options:"
        echo "  --with-sample-data    Insert sample data after migration"
        echo "  --help, -h           Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac