from fastapi import FastAPI
from contextlib import asynccontextmanager
import grpc
from concurrent import futures
import asyncio
import uvloop
import os
import logging

from app.grpc_server import ProductServicer
from app.database import init_db
from app.proto import product_pb2_grpc

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    logger.info("Product service started")
    yield
    # 关闭时清理资源
    logger.info("Product service shutting down")

# 创建FastAPI应用（用于健康检查）
app = FastAPI(
    title="Product Service",
    description="商品管理服务",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "product-service"}

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Product Service is running"}

async def serve_grpc():
    """启动gRPC服务器"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductServicer(), server)
    
    listen_addr = '0.0.0.0:50052'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await server.stop(5)

async def serve_http():
    """启动HTTP服务器"""
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """主函数"""
    # 使用uvloop提升性能
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # 并发启动gRPC和HTTP服务器
    await asyncio.gather(
        serve_grpc(),
        serve_http()
    )

if __name__ == "__main__":
    asyncio.run(main())
