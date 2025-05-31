from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, func, Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    store_id = Column(BigInteger, nullable=False, index=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_amount = Column(BigInteger, nullable=False)  # Total in cents
    shipping_fee = Column(BigInteger, default=0)  # Shipping fee in cents
    tax_amount = Column(BigInteger, default=0)  # Tax in cents
    discount_amount = Column(BigInteger, default=0)  # Discount in cents
    final_amount = Column(BigInteger, nullable=False)  # Final amount after discounts
    
    # Shipping address
    shipping_name = Column(String(100), nullable=False)
    shipping_phone = Column(String(20), nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_country = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    
    # Tracking information
    tracking_number = Column(String(100))
    shipping_company = Column(String(100))
    estimated_delivery = Column(DateTime(timezone=True))
    
    # Order notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Relationship
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    product_id = Column(BigInteger, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_image = Column(String(500))
    quantity = Column(Integer, nullable=False)
    price = Column(BigInteger, nullable=False)  # Unit price in cents
    total_price = Column(BigInteger, nullable=False)  # Total price in cents
    product_attributes = Column(Text)  # JSON string of product attributes
    
    # Relationship
    order = relationship("Order", back_populates="items")
