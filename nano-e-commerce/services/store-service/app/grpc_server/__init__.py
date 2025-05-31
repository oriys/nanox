import grpc
from concurrent import futures
import logging
from app.proto import store_pb2_grpc, store_pb2
from app.service import StoreService
from app.database import get_db

logger = logging.getLogger(__name__)

class StoreServicer(store_pb2_grpc.StoreServiceServicer):
    def __init__(self):
        self.store_service = StoreService()
    
    async def CreateStore(self, request: store_pb2.CreateStoreRequest, context) -> store_pb2.CreateStoreResponse:
        """Create a new store"""
        async for db in get_db():
            return await self.store_service.create_store(db, request)
    
    async def GetStore(self, request: store_pb2.GetStoreRequest, context) -> store_pb2.GetStoreResponse:
        """Get store by ID"""
        async for db in get_db():
            return await self.store_service.get_store(db, request)
    
    async def GetUserStores(self, request: store_pb2.GetUserStoresRequest, context) -> store_pb2.GetUserStoresResponse:
        """Get stores owned by user"""
        # TODO: Implement user stores logic
        return store_pb2.GetUserStoresResponse(
            success=False,
            message="Not implemented yet"
        )
    
    async def UpdateStore(self, request: store_pb2.UpdateStoreRequest, context) -> store_pb2.UpdateStoreResponse:
        """Update store"""
        # TODO: Implement update store logic
        return store_pb2.UpdateStoreResponse(
            success=False,
            message="Not implemented yet"
        )
    
    async def DeleteStore(self, request: store_pb2.DeleteStoreRequest, context) -> store_pb2.DeleteStoreResponse:
        """Delete store"""
        # TODO: Implement delete store logic
        return store_pb2.DeleteStoreResponse(
            success=False,
            message="Not implemented yet"
        )

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    store_pb2_grpc.add_StoreServiceServicer_to_server(StoreServicer(), server)
    
    listen_addr = '[::]:50056'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(0)
