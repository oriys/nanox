from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, func, Enum as SQLEnum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class PaymentMethod(enum.Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PAYPAL = "PAYPAL"
    STRIPE = "STRIPE"
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_id = Column(String(100), unique=True, nullable=False, index=True)  # External payment ID
    order_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False, default="USD")
    method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Payment gateway specific fields
    gateway_payment_id = Column(String(200))  # Payment ID from gateway (Stripe, PayPal, etc)
    gateway_response = Column(Text)  # JSON response from gateway
    
    # Card information (encrypted/tokenized)
    card_last_four = Column(String(4))
    card_brand = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Failure information
    failure_reason = Column(String(500))
    failure_code = Column(String(50))

class Refund(Base):
    __tablename__ = "refunds"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    refund_id = Column(String(100), unique=True, nullable=False, index=True)
    payment_id = Column(BigInteger, nullable=False, index=True)
    order_id = Column(BigInteger, nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)  # Refund amount in cents
    reason = Column(String(500))
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Gateway specific
    gateway_refund_id = Column(String(200))
    gateway_response = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
