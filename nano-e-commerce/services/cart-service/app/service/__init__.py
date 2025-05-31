import redis
import json
import grpc
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from sqlalchemy.dialects.postgresql import insert
from app.models import CartItem
from app.proto import cart_pb2, cart_pb2_grpc
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CartService:
    def __init__(self):
        # Redis for caching cart data
        self.redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    def _get_cache_key(self, user_id: int) -> str:
        return f"cart:user:{user_id}"
    
    async def _invalidate_cache(self, user_id: int):
        """Invalidate user's cart cache"""
        cache_key = self._get_cache_key(user_id)
        self.redis_client.delete(cache_key)
    
    async def _get_product_info(self, product_id: int) -> Optional[dict]:
        """Get product info from product service (simplified for now)"""
        # TODO: Make gRPC call to product service
        # For now, return mock data
        return {
            "name": f"Product {product_id}",
            "price": 2999,  # $29.99 in cents
            "image": f"/images/product_{product_id}.jpg"
        }
    
    async def add_item(self, db: AsyncSession, request: cart_pb2.AddItemRequest) -> cart_pb2.AddItemResponse:
        """Add item to cart or update quantity if exists"""
        try:
            # Get product info
            product_info = await self._get_product_info(request.product_id)
            if not product_info:
                return cart_pb2.AddItemResponse(
                    success=False,
                    message="Product not found"
                )
            
            # Check if item already exists in cart
            existing_item = await db.execute(
                select(CartItem).where(
                    and_(
                        CartItem.user_id == request.user_id,
                        CartItem.product_id == request.product_id
                    )
                )
            )
            existing_item = existing_item.scalar_one_or_none()
            
            if existing_item:
                # Update quantity
                existing_item.quantity += request.quantity
                existing_item.updated_at = datetime.utcnow()
            else:
                # Create new cart item
                cart_item = CartItem(
                    user_id=request.user_id,
                    product_id=request.product_id,
                    quantity=request.quantity,
                    price=product_info["price"],
                    product_name=product_info["name"],
                    product_image=product_info["image"],
                    selected=True
                )
                db.add(cart_item)
            
            await db.commit()
            await self._invalidate_cache(request.user_id)
            
            return cart_pb2.AddItemResponse(
                success=True,
                message="Item added to cart successfully"
            )
            
        except Exception as e:
            logger.error(f"Error adding item to cart: {e}")
            await db.rollback()
            return cart_pb2.AddItemResponse(
                success=False,
                message="Failed to add item to cart"
            )
    
    async def update_item(self, db: AsyncSession, request: cart_pb2.UpdateItemRequest) -> cart_pb2.UpdateItemResponse:
        """Update cart item quantity or selection status"""
        try:
            item = await db.execute(
                select(CartItem).where(
                    and_(
                        CartItem.user_id == request.user_id,
                        CartItem.product_id == request.product_id
                    )
                )
            )
            item = item.scalar_one_or_none()
            
            if not item:
                return cart_pb2.UpdateItemResponse(
                    success=False,
                    message="Item not found in cart"
                )
            
            if request.quantity > 0:
                item.quantity = request.quantity
            
            if hasattr(request, 'selected'):
                item.selected = request.selected
            
            item.updated_at = datetime.utcnow()
            
            await db.commit()
            await self._invalidate_cache(request.user_id)
            
            return cart_pb2.UpdateItemResponse(
                success=True,
                message="Item updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            await db.rollback()
            return cart_pb2.UpdateItemResponse(
                success=False,
                message="Failed to update item"
            )
    
    async def remove_item(self, db: AsyncSession, request: cart_pb2.RemoveItemRequest) -> cart_pb2.RemoveItemResponse:
        """Remove item from cart"""
        try:
            await db.execute(
                delete(CartItem).where(
                    and_(
                        CartItem.user_id == request.user_id,
                        CartItem.product_id == request.product_id
                    )
                )
            )
            
            await db.commit()
            await self._invalidate_cache(request.user_id)
            
            return cart_pb2.RemoveItemResponse(
                success=True,
                message="Item removed from cart"
            )
            
        except Exception as e:
            logger.error(f"Error removing cart item: {e}")
            await db.rollback()
            return cart_pb2.RemoveItemResponse(
                success=False,
                message="Failed to remove item"
            )
    
    async def get_cart(self, db: AsyncSession, request: cart_pb2.GetCartRequest) -> cart_pb2.GetCartResponse:
        """Get user's cart details"""
        try:
            # Try to get from cache first
            cache_key = self._get_cache_key(request.user_id)
            cached_cart = self.redis_client.get(cache_key)
            
            if cached_cart:
                cart_data = json.loads(cached_cart)
                # Convert to protobuf response
                cart_items = []
                for item_data in cart_data['items']:
                    cart_item = cart_pb2.CartItem(
                        id=item_data['id'],
                        user_id=item_data['user_id'],
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        product_name=item_data['product_name'],
                        product_image=item_data['product_image'],
                        selected=item_data['selected'],
                        created_at=item_data['created_at'],
                        updated_at=item_data['updated_at']
                    )
                    cart_items.append(cart_item)
                
                cart = cart_pb2.Cart(
                    user_id=request.user_id,
                    items=cart_items,
                    total_count=cart_data['total_count'],
                    total_amount=cart_data['total_amount'],
                    total_selected_count=cart_data['total_selected_count']
                )
                
                return cart_pb2.GetCartResponse(
                    success=True,
                    cart=cart
                )
            
            # Get from database
            items_result = await db.execute(
                select(CartItem).where(CartItem.user_id == request.user_id)
            )
            items = items_result.scalars().all()
            
            # Convert to protobuf objects
            cart_items = []
            total_count = 0
            total_amount = 0
            total_selected_count = 0
            
            cache_data = {
                'items': [],
                'total_count': 0,
                'total_amount': 0,
                'total_selected_count': 0
            }
            
            for item in items:
                cart_item = cart_pb2.CartItem(
                    id=item.id,
                    user_id=item.user_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                    product_name=item.product_name,
                    product_image=item.product_image or "",
                    selected=item.selected,
                    created_at=int(item.created_at.timestamp()) if item.created_at else 0,
                    updated_at=int(item.updated_at.timestamp()) if item.updated_at else 0
                )
                cart_items.append(cart_item)
                
                total_count += item.quantity
                if item.selected:
                    total_amount += item.price * item.quantity
                    total_selected_count += item.quantity
                
                # Prepare cache data
                cache_data['items'].append({
                    'id': item.id,
                    'user_id': item.user_id,
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': item.price,
                    'product_name': item.product_name,
                    'product_image': item.product_image or "",
                    'selected': item.selected,
                    'created_at': int(item.created_at.timestamp()) if item.created_at else 0,
                    'updated_at': int(item.updated_at.timestamp()) if item.updated_at else 0
                })
            
            cache_data.update({
                'total_count': total_count,
                'total_amount': total_amount,
                'total_selected_count': total_selected_count
            })
            
            # Cache the result for 5 minutes
            self.redis_client.setex(cache_key, 300, json.dumps(cache_data))
            
            cart = cart_pb2.Cart(
                user_id=request.user_id,
                items=cart_items,
                total_count=total_count,
                total_amount=total_amount,
                total_selected_count=total_selected_count
            )
            
            return cart_pb2.GetCartResponse(
                success=True,
                cart=cart
            )
            
        except Exception as e:
            logger.error(f"Error getting cart: {e}")
            return cart_pb2.GetCartResponse(
                success=False,
                message="Failed to get cart"
            )
    
    async def clear_cart(self, db: AsyncSession, request: cart_pb2.ClearCartRequest) -> cart_pb2.ClearCartResponse:
        """Clear all items from user's cart"""
        try:
            await db.execute(
                delete(CartItem).where(CartItem.user_id == request.user_id)
            )
            
            await db.commit()
            await self._invalidate_cache(request.user_id)
            
            return cart_pb2.ClearCartResponse(
                success=True,
                message="Cart cleared successfully"
            )
            
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            await db.rollback()
            return cart_pb2.ClearCartResponse(
                success=False,
                message="Failed to clear cart"
            )
    
    async def get_cart_count(self, db: AsyncSession, request: cart_pb2.GetCartCountRequest) -> cart_pb2.GetCartCountResponse:
        """Get total count of items in user's cart"""
        try:
            result = await db.execute(
                select(func.sum(CartItem.quantity)).where(CartItem.user_id == request.user_id)
            )
            count = result.scalar() or 0
            
            return cart_pb2.GetCartCountResponse(
                success=True,
                count=count
            )
            
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return cart_pb2.GetCartCountResponse(
                success=False,
                count=0
            )
