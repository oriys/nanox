from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Category(Base):
    """商品分类模型"""
    __tablename__ = "categories"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(BigInteger, ForeignKey("categories.id"), nullable=True)
    image = Column(String(255))
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, inactive
    created_at = Column(BigInteger, default=lambda: int(func.now().timestamp()))
    updated_at = Column(BigInteger, default=lambda: int(func.now().timestamp()), onupdate=lambda: int(func.now().timestamp()))

    # 自关联关系
    parent = relationship("Category", remote_side=[id], backref="children")
    # 关联商品
    products = relationship("Product", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "image": self.image,
            "sort_order": self.sort_order,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Product(Base):
    """商品模型"""
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    images = Column(JSON)  # 存储图片URL列表
    price = Column(BigInteger, nullable=False)  # 价格，单位：分
    category_id = Column(BigInteger, ForeignKey("categories.id"), nullable=False)
    store_id = Column(BigInteger, nullable=False, index=True)
    stock = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, inactive, deleted
    attributes = Column(JSON)  # 商品属性，如颜色、尺寸等
    created_at = Column(BigInteger, default=lambda: int(func.now().timestamp()))
    updated_at = Column(BigInteger, default=lambda: int(func.now().timestamp()), onupdate=lambda: int(func.now().timestamp()))

    # 关联分类
    category = relationship("Category", back_populates="products")
    # 关联库存预留
    stock_reservations = relationship("StockReservation", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "images": self.images or [],
            "price": self.price,
            "category_id": self.category_id,
            "store_id": self.store_id,
            "stock": self.stock,
            "status": self.status,
            "attributes": self.attributes or {},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class StockReservation(Base):
    """库存预留模型"""
    __tablename__ = "stock_reservations"

    id = Column(BigInteger, primary_key=True, index=True)
    reservation_id = Column(String(100), unique=True, nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default="reserved")  # reserved, confirmed, released
    expires_at = Column(BigInteger, nullable=False)  # 过期时间戳
    created_at = Column(BigInteger, default=lambda: int(func.now().timestamp()))
    updated_at = Column(BigInteger, default=lambda: int(func.now().timestamp()), onupdate=lambda: int(func.now().timestamp()))

    # 关联商品
    product = relationship("Product", back_populates="stock_reservations")

    def to_dict(self):
        return {
            "id": self.id,
            "reservation_id": self.reservation_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "order_id": self.order_id,
            "status": self.status,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
