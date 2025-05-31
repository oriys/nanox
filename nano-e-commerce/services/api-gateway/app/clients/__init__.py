import grpc
import os
from app.proto import user_pb2_grpc, product_pb2_grpc, cart_pb2_grpc, order_pb2_grpc, payment_pb2_grpc, store_pb2_grpc

class GRPCClients:
    def __init__(self):
        # Service addresses
        self.user_service_addr = os.getenv("USER_SERVICE_ADDR", "user-service:50051")
        self.product_service_addr = os.getenv("PRODUCT_SERVICE_ADDR", "product-service:50052")
        self.cart_service_addr = os.getenv("CART_SERVICE_ADDR", "cart-service:50053")
        self.order_service_addr = os.getenv("ORDER_SERVICE_ADDR", "order-service:50054")
        self.payment_service_addr = os.getenv("PAYMENT_SERVICE_ADDR", "payment-service:50055")
        self.store_service_addr = os.getenv("STORE_SERVICE_ADDR", "store-service:50056")
        
        # Initialize channels
        self.user_channel = grpc.aio.insecure_channel(self.user_service_addr)
        self.product_channel = grpc.aio.insecure_channel(self.product_service_addr)
        self.cart_channel = grpc.aio.insecure_channel(self.cart_service_addr)
        self.order_channel = grpc.aio.insecure_channel(self.order_service_addr)
        self.payment_channel = grpc.aio.insecure_channel(self.payment_service_addr)
        self.store_channel = grpc.aio.insecure_channel(self.store_service_addr)
        
        # Initialize stubs
        self.user_stub = user_pb2_grpc.UserServiceStub(self.user_channel)
        self.product_stub = product_pb2_grpc.ProductServiceStub(self.product_channel)
        self.cart_stub = cart_pb2_grpc.CartServiceStub(self.cart_channel)
        self.order_stub = order_pb2_grpc.OrderServiceStub(self.order_channel)
        self.payment_stub = payment_pb2_grpc.PaymentServiceStub(self.payment_channel)
        self.store_stub = store_pb2_grpc.StoreServiceStub(self.store_channel)
    
    async def close(self):
        """Close all gRPC channels"""
        await self.user_channel.close()
        await self.product_channel.close()
        await self.cart_channel.close()
        await self.order_channel.close()
        await self.payment_channel.close()
        await self.store_channel.close()

# Global clients instance
grpc_clients = GRPCClients()
