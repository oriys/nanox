import grpc
from concurrent import futures
import logging
from app.proto import order_pb2_grpc, order_pb2
from app.service import OrderService
from app.database import get_db

logger = logging.getLogger(__name__)

class OrderServicer(order_pb2_grpc.OrderServiceServicer):
    def __init__(self):
        self.order_service = OrderService()
    
    async def CreateOrder(self, request: order_pb2.CreateOrderRequest, context) -> order_pb2.CreateOrderResponse:
        """Create a new order"""
        async for db in get_db():
            return await self.order_service.create_order(db, request)
    
    async def GetOrder(self, request: order_pb2.GetOrderRequest, context) -> order_pb2.GetOrderResponse:
        """Get order by ID"""
        async for db in get_db():
            return await self.order_service.get_order(db, request)
    
    async def GetUserOrders(self, request: order_pb2.GetUserOrdersRequest, context) -> order_pb2.GetUserOrdersResponse:
        """Get user orders"""
        async for db in get_db():
            return await self.order_service.get_user_orders(db, request)
    
    async def GetStoreOrders(self, request: order_pb2.GetStoreOrdersRequest, context) -> order_pb2.GetStoreOrdersResponse:
        """Get store orders"""
        # TODO: Implement store orders logic
        return order_pb2.GetStoreOrdersResponse(
            success=False,
            message="Not implemented yet"
        )
    
    async def UpdateOrderStatus(self, request: order_pb2.UpdateOrderStatusRequest, context) -> order_pb2.UpdateOrderStatusResponse:
        """Update order status"""
        async for db in get_db():
            return await self.order_service.update_order_status(db, request)
    
    async def CancelOrder(self, request: order_pb2.CancelOrderRequest, context) -> order_pb2.CancelOrderResponse:
        """Cancel order"""
        # TODO: Implement cancel order logic
        return order_pb2.CancelOrderResponse(
            success=False,
            message="Not implemented yet"
        )
    
    async def ConfirmOrder(self, request: order_pb2.ConfirmOrderRequest, context) -> order_pb2.ConfirmOrderResponse:
        """Confirm order delivery"""
        # TODO: Implement confirm order logic
        return order_pb2.ConfirmOrderResponse(
            success=False,
            message="Not implemented yet"
        )
    
    async def AddShipping(self, request: order_pb2.AddShippingRequest, context) -> order_pb2.AddShippingResponse:
        """Add shipping information"""
        async for db in get_db():
            return await self.order_service.add_shipping(db, request)

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServicer(), server)
    
    listen_addr = '[::]:50054'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(0)
