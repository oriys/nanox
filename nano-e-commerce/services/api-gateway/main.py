import asyncio
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.routes import auth, products, cart, orders, payments, stores
from app.clients import grpc_clients

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting API Gateway")
    yield
    # Shutdown
    logger.info("Shutting down API Gateway")
    await grpc_clients.close()

# Create FastAPI app
app = FastAPI(
    title="E-commerce API Gateway",
    description="Headless e-commerce platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)

@app.get("/")
async def root():
    return {
        "message": "E-commerce API Gateway",
        "version": "1.0.0",
        "services": {
            "user": "user-service:50051",
            "product": "product-service:50052",
            "cart": "cart-service:50053",
            "order": "order-service:50054",
            "payment": "payment-service:50055",
            "store": "store-service:50056"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}

async def main():
    """Main function to run the API Gateway"""
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
