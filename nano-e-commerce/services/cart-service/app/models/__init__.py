from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Index, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class CartItem(Base):
    __tablename__ = "cart_items"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    product_id = Column(BigInteger, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(BigInteger, nullable=False)  # Price in cents when added to cart
    product_name = Column(String(255), nullable=False)
    product_image = Column(String(500))
    selected = Column(Boolean, default=True)  # Whether item is selected for checkout
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Unique constraint to prevent duplicate product per user
    __table_args__ = (
        Index('idx_user_product', 'user_id', 'product_id', unique=True),
        Index('idx_user_id', 'user_id'),
        Index('idx_product_id', 'product_id'),
    )
