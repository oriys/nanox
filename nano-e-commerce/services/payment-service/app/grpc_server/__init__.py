import grpc
from concurrent import futures
import logging
from app.proto import payment_pb2_grpc, payment_pb2
from app.service import PaymentService
from app.database import get_db

logger = logging.getLogger(__name__)

class PaymentServicer(payment_pb2_grpc.PaymentServiceServicer):
    def __init__(self):
        self.payment_service = PaymentService()
    
    async def CreatePayment(self, request: payment_pb2.CreatePaymentRequest, context) -> payment_pb2.CreatePaymentResponse:
        """Create and process a payment"""
        async for db in get_db():
            return await self.payment_service.create_payment(db, request)
    
    async def GetPayment(self, request: payment_pb2.GetPaymentRequest, context) -> payment_pb2.GetPaymentResponse:
        """Get payment by ID"""
        async for db in get_db():
            return await self.payment_service.get_payment(db, request)
    
    async def GetOrderPayments(self, request: payment_pb2.GetOrderPaymentsRequest, context) -> payment_pb2.GetOrderPaymentsResponse:
        """Get all payments for an order"""
        async for db in get_db():
            return await self.payment_service.get_order_payments(db, request)
    
    async def RefundPayment(self, request: payment_pb2.RefundPaymentRequest, context) -> payment_pb2.RefundPaymentResponse:
        """Process a refund"""
        async for db in get_db():
            return await self.payment_service.refund_payment(db, request)
    
    async def GetUserPayments(self, request: payment_pb2.GetUserPaymentsRequest, context) -> payment_pb2.GetUserPaymentsResponse:
        """Get user payments"""
        # TODO: Implement user payments logic
        return payment_pb2.GetUserPaymentsResponse(
            success=False,
            message="Not implemented yet"
        )

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServicer(), server)
    
    listen_addr = '[::]:50055'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(0)
