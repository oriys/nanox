import json
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.models import Order, OrderItem, OrderStatus
from app.proto import order_pb2, order_pb2_grpc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self):
        pass
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"ORD{timestamp}{unique_id}"
    
    def _convert_order_to_proto(self, order: Order) -> order_pb2.Order:
        """Convert SQLAlchemy Order to protobuf Order"""
        order_items = []
        for item in order.items:
            order_item = order_pb2.OrderItem(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_image=item.product_image or "",
                quantity=item.quantity,
                price=item.price,
                total_price=item.total_price
            )
            if item.product_attributes:
                try:
                    attrs = json.loads(item.product_attributes)
                    order_item.product_attributes.update(attrs)
                except:
                    pass
            order_items.append(order_item)
        
        shipping_address = order_pb2.ShippingAddress(
            name=order.shipping_name,
            phone=order.shipping_phone,
            address=order.shipping_address,
            city=order.shipping_city,
            state=order.shipping_state,
            country=order.shipping_country,
            postal_code=order.shipping_postal_code
        )
        
        shipping_info = order_pb2.ShippingInfo()
        if order.tracking_number:
            shipping_info.tracking_number = order.tracking_number
        if order.shipping_company:
            shipping_info.shipping_company = order.shipping_company
        if order.estimated_delivery:
            shipping_info.estimated_delivery = int(order.estimated_delivery.timestamp())
        
        # Convert status enum
        status_map = {
            OrderStatus.PENDING: order_pb2.PENDING,
            OrderStatus.PAID: order_pb2.PAID,
            OrderStatus.SHIPPED: order_pb2.SHIPPED,
            OrderStatus.DELIVERED: order_pb2.DELIVERED,
            OrderStatus.COMPLETED: order_pb2.COMPLETED,
            OrderStatus.CANCELLED: order_pb2.CANCELLED,
            OrderStatus.REFUNDED: order_pb2.REFUNDED,
        }
        
        return order_pb2.Order(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            store_id=order.store_id,
            status=status_map.get(order.status, order_pb2.PENDING),
            total_amount=order.total_amount,
            shipping_fee=order.shipping_fee,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            final_amount=order.final_amount,
            shipping_address=shipping_address,
            shipping_info=shipping_info,
            notes=order.notes or "",
            items=order_items,
            created_at=int(order.created_at.timestamp()) if order.created_at else 0,
            updated_at=int(order.updated_at.timestamp()) if order.updated_at else 0,
            shipped_at=int(order.shipped_at.timestamp()) if order.shipped_at else 0,
            delivered_at=int(order.delivered_at.timestamp()) if order.delivered_at else 0
        )
    
    async def create_order(self, db: AsyncSession, request: order_pb2.CreateOrderRequest) -> order_pb2.CreateOrderResponse:
        """Create a new order"""
        try:
            # Generate order number
            order_number = self._generate_order_number()
            
            # Calculate totals
            total_amount = sum(item.price * item.quantity for item in request.items)
            final_amount = total_amount + request.shipping_fee + request.tax_amount - request.discount_amount
            
            # Create order
            order = Order(
                order_number=order_number,
                user_id=request.user_id,
                store_id=request.store_id,
                status=OrderStatus.PENDING,
                total_amount=total_amount,
                shipping_fee=request.shipping_fee,
                tax_amount=request.tax_amount,
                discount_amount=request.discount_amount,
                final_amount=final_amount,
                shipping_name=request.shipping_address.name,
                shipping_phone=request.shipping_address.phone,
                shipping_address=request.shipping_address.address,
                shipping_city=request.shipping_address.city,
                shipping_state=request.shipping_address.state,
                shipping_country=request.shipping_address.country,
                shipping_postal_code=request.shipping_address.postal_code,
                notes=request.notes
            )
            
            db.add(order)
            await db.flush()  # Get order ID
            
            # Create order items
            for item in request.items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_image=item.product_image,
                    quantity=item.quantity,
                    price=item.price,
                    total_price=item.price * item.quantity,
                    product_attributes=json.dumps(dict(item.product_attributes)) if item.product_attributes else None
                )
                db.add(order_item)
            
            await db.commit()
            
            # Fetch the complete order with items
            result = await db.execute(
                select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
            )
            created_order = result.scalar_one()
            
            return order_pb2.CreateOrderResponse(
                success=True,
                order=self._convert_order_to_proto(created_order),
                message="Order created successfully"
            )
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            await db.rollback()
            return order_pb2.CreateOrderResponse(
                success=False,
                message="Failed to create order"
            )
    
    async def get_order(self, db: AsyncSession, request: order_pb2.GetOrderRequest) -> order_pb2.GetOrderResponse:
        """Get order by ID"""
        try:
            result = await db.execute(
                select(Order).options(selectinload(Order.items)).where(Order.id == request.order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return order_pb2.GetOrderResponse(
                    success=False,
                    message="Order not found"
                )
            
            return order_pb2.GetOrderResponse(
                success=True,
                order=self._convert_order_to_proto(order)
            )
            
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return order_pb2.GetOrderResponse(
                success=False,
                message="Failed to get order"
            )
    
    async def get_user_orders(self, db: AsyncSession, request: order_pb2.GetUserOrdersRequest) -> order_pb2.GetUserOrdersResponse:
        """Get orders for a user"""
        try:
            query = select(Order).options(selectinload(Order.items)).where(Order.user_id == request.user_id)
            
            # Add status filter if provided
            if request.status != order_pb2.PENDING:  # Assuming PENDING is default/unspecified
                status_map = {
                    order_pb2.PENDING: OrderStatus.PENDING,
                    order_pb2.PAID: OrderStatus.PAID,
                    order_pb2.SHIPPED: OrderStatus.SHIPPED,
                    order_pb2.DELIVERED: OrderStatus.DELIVERED,
                    order_pb2.COMPLETED: OrderStatus.COMPLETED,
                    order_pb2.CANCELLED: OrderStatus.CANCELLED,
                    order_pb2.REFUNDED: OrderStatus.REFUNDED,
                }
                if request.status in status_map:
                    query = query.where(Order.status == status_map[request.status])
            
            # Add pagination
            if request.page > 0 and request.page_size > 0:
                offset = (request.page - 1) * request.page_size
                query = query.offset(offset).limit(request.page_size)
            
            query = query.order_by(desc(Order.created_at))
            
            result = await db.execute(query)
            orders = result.scalars().all()
            
            order_list = [self._convert_order_to_proto(order) for order in orders]
            
            return order_pb2.GetUserOrdersResponse(
                success=True,
                orders=order_list,
                total_count=len(order_list)
            )
            
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return order_pb2.GetUserOrdersResponse(
                success=False,
                message="Failed to get user orders"
            )
    
    async def update_order_status(self, db: AsyncSession, request: order_pb2.UpdateOrderStatusRequest) -> order_pb2.UpdateOrderStatusResponse:
        """Update order status"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == request.order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return order_pb2.UpdateOrderStatusResponse(
                    success=False,
                    message="Order not found"
                )
            
            # Convert protobuf status to SQLAlchemy enum
            status_map = {
                order_pb2.PENDING: OrderStatus.PENDING,
                order_pb2.PAID: OrderStatus.PAID,
                order_pb2.SHIPPED: OrderStatus.SHIPPED,
                order_pb2.DELIVERED: OrderStatus.DELIVERED,
                order_pb2.COMPLETED: OrderStatus.COMPLETED,
                order_pb2.CANCELLED: OrderStatus.CANCELLED,
                order_pb2.REFUNDED: OrderStatus.REFUNDED,
            }
            
            if request.status not in status_map:
                return order_pb2.UpdateOrderStatusResponse(
                    success=False,
                    message="Invalid status"
                )
            
            old_status = order.status
            order.status = status_map[request.status]
            order.updated_at = datetime.utcnow()
            
            # Update specific timestamps
            if request.status == order_pb2.SHIPPED and old_status != OrderStatus.SHIPPED:
                order.shipped_at = datetime.utcnow()
            elif request.status == order_pb2.DELIVERED and old_status != OrderStatus.DELIVERED:
                order.delivered_at = datetime.utcnow()
            
            await db.commit()
            
            return order_pb2.UpdateOrderStatusResponse(
                success=True,
                message="Order status updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            await db.rollback()
            return order_pb2.UpdateOrderStatusResponse(
                success=False,
                message="Failed to update order status"
            )
    
    async def add_shipping(self, db: AsyncSession, request: order_pb2.AddShippingRequest) -> order_pb2.AddShippingResponse:
        """Add shipping information to order"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == request.order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return order_pb2.AddShippingResponse(
                    success=False,
                    message="Order not found"
                )
            
            order.tracking_number = request.tracking_number
            order.shipping_company = request.shipping_company
            if request.estimated_delivery > 0:
                order.estimated_delivery = datetime.fromtimestamp(request.estimated_delivery)
            
            # Update status to shipped if not already
            if order.status == OrderStatus.PAID:
                order.status = OrderStatus.SHIPPED
                order.shipped_at = datetime.utcnow()
            
            order.updated_at = datetime.utcnow()
            
            await db.commit()
            
            return order_pb2.AddShippingResponse(
                success=True,
                message="Shipping information added successfully"
            )
            
        except Exception as e:
            logger.error(f"Error adding shipping info: {e}")
            await db.rollback()
            return order_pb2.AddShippingResponse(
                success=False,
                message="Failed to add shipping information"
            )
