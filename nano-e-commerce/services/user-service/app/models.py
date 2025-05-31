from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(BigInteger, default=lambda: int(func.now().timestamp()))
    updated_at = Column(BigInteger, default=lambda: int(func.now().timestamp()), onupdate=lambda: int(func.now().timestamp()))

    # 关联地址
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "avatar": self.avatar,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Address(Base):
    """地址模型"""
    __tablename__ = "addresses"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)  # 收货人姓名
    phone = Column(String(20), nullable=False)  # 收货人电话
    province = Column(String(50), nullable=False)  # 省份
    city = Column(String(50), nullable=False)  # 城市
    district = Column(String(50), nullable=False)  # 区/县
    detail = Column(String(255), nullable=False)  # 详细地址
    postal_code = Column(String(10))  # 邮政编码
    is_default = Column(Boolean, default=False)  # 是否默认地址
    created_at = Column(BigInteger, default=lambda: int(func.now().timestamp()))
    updated_at = Column(BigInteger, default=lambda: int(func.now().timestamp()), onupdate=lambda: int(func.now().timestamp()))

    # 关联用户
    user = relationship("User", back_populates="addresses")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "detail": self.detail,
            "postal_code": self.postal_code,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
