from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Store
from app.proto import store_pb2, store_pb2_grpc
import logging

logger = logging.getLogger(__name__)

class StoreService:
    def __init__(self):
        pass
    
    def _convert_store_to_proto(self, store: Store) -> store_pb2.Store:
        """Convert SQLAlchemy Store to protobuf Store"""
        return store_pb2.Store(
            id=store.id,
            name=store.name,
            description=store.description or "",
            owner_id=store.owner_id,
            email=store.email,
            phone=store.phone or "",
            website=store.website or "",
            logo_url=store.logo_url or "",
            address=store.address or "",
            city=store.city or "",
            state=store.state or "",
            country=store.country or "",
            postal_code=store.postal_code or "",
            tax_id=store.tax_id or "",
            business_license=store.business_license or "",
            is_active=store.is_active,
            is_verified=store.is_verified,
            created_at=int(store.created_at.timestamp()) if store.created_at else 0,
            updated_at=int(store.updated_at.timestamp()) if store.updated_at else 0
        )
    
    async def create_store(self, db: AsyncSession, request: store_pb2.CreateStoreRequest) -> store_pb2.CreateStoreResponse:
        """Create a new store"""
        try:
            store = Store(
                name=request.name,
                description=request.description,
                owner_id=request.owner_id,
                email=request.email,
                phone=request.phone,
                website=request.website,
                address=request.address,
                city=request.city,
                state=request.state,
                country=request.country,
                postal_code=request.postal_code,
                tax_id=request.tax_id,
                business_license=request.business_license
            )
            
            db.add(store)
            await db.commit()
            await db.refresh(store)
            
            return store_pb2.CreateStoreResponse(
                success=True,
                store=self._convert_store_to_proto(store),
                message="Store created successfully"
            )
            
        except Exception as e:
            logger.error(f"Error creating store: {e}")
            await db.rollback()
            return store_pb2.CreateStoreResponse(
                success=False,
                message="Failed to create store"
            )
    
    async def get_store(self, db: AsyncSession, request: store_pb2.GetStoreRequest) -> store_pb2.GetStoreResponse:
        """Get store by ID"""
        try:
            result = await db.execute(
                select(Store).where(Store.id == request.store_id)
            )
            store = result.scalar_one_or_none()
            
            if not store:
                return store_pb2.GetStoreResponse(
                    success=False,
                    message="Store not found"
                )
            
            return store_pb2.GetStoreResponse(
                success=True,
                store=self._convert_store_to_proto(store)
            )
            
        except Exception as e:
            logger.error(f"Error getting store: {e}")
            return store_pb2.GetStoreResponse(
                success=False,
                message="Failed to get store"
            )
