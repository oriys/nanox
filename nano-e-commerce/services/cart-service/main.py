import asyncio
import logging
from fastapi import FastAPI
import uvicorn
from app.grpc_server import serve as grpc_serve
from app.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app for health checks
app = FastAPI(title="Cart Service", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cart-service"}

@app.get("/")
async def root():
    return {"message": "Cart Service is running"}

async def run_fastapi():
    """Run FastAPI server"""
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8003, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Main function to run both gRPC and HTTP servers"""
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Run both servers concurrently
    await asyncio.gather(
        grpc_serve(),
        run_fastapi()
    )

if __name__ == "__main__":
    asyncio.run(main())
