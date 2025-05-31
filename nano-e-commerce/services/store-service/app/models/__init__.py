from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Store(Base):
    __tablename__ = "stores"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(BigInteger, nullable=False, index=True)  # User ID of store owner
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    website = Column(String(500))
    logo_url = Column(String(500))
    
    # Address information
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Business information
    tax_id = Column(String(50))
    business_license = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
