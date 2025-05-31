import grpc
from concurrent import futures
import logging
from app.proto import cart_pb2_grpc, cart_pb2
from app.service import CartService
from app.database import get_db

logger = logging.getLogger(__name__)

class CartServicer(cart_pb2_grpc.CartServiceServicer):
    def __init__(self):
        self.cart_service = CartService()
    
    async def AddItem(self, request: cart_pb2.AddItemRequest, context) -> cart_pb2.AddItemResponse:
        """Add item to cart"""
        async for db in get_db():
            return await self.cart_service.add_item(db, request)
    
    async def UpdateItem(self, request: cart_pb2.UpdateItemRequest, context) -> cart_pb2.UpdateItemResponse:
        """Update cart item"""
        async for db in get_db():
            return await self.cart_service.update_item(db, request)
    
    async def RemoveItem(self, request: cart_pb2.RemoveItemRequest, context) -> cart_pb2.RemoveItemResponse:
        """Remove item from cart"""
        async for db in get_db():
            return await self.cart_service.remove_item(db, request)
    
    async def GetCart(self, request: cart_pb2.GetCartRequest, context) -> cart_pb2.GetCartResponse:
        """Get cart details"""
        async for db in get_db():
            return await self.cart_service.get_cart(db, request)
    
    async def ClearCart(self, request: cart_pb2.ClearCartRequest, context) -> cart_pb2.ClearCartResponse:
        """Clear cart"""
        async for db in get_db():
            return await self.cart_service.clear_cart(db, request)
    
    async def GetCartCount(self, request: cart_pb2.GetCartCountRequest, context) -> cart_pb2.GetCartCountResponse:
        """Get cart count"""
        async for db in get_db():
            return await self.cart_service.get_cart_count(db, request)

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    cart_pb2_grpc.add_CartServiceServicer_to_server(CartServicer(), server)
    
    listen_addr = '[::]:50053'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(0)
