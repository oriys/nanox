import json
import uuid
import stripe
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Payment, Refund, PaymentStatus, PaymentMethod
from app.proto import payment_pb2, payment_pb2_grpc
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

class PaymentService:
    def __init__(self):
        pass
    
    def _generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        return f"PAY_{uuid.uuid4().hex[:16].upper()}"
    
    def _generate_refund_id(self) -> str:
        """Generate unique refund ID"""
        return f"REF_{uuid.uuid4().hex[:16].upper()}"
    
    def _convert_payment_to_proto(self, payment: Payment) -> payment_pb2.Payment:
        """Convert SQLAlchemy Payment to protobuf Payment"""
        # Convert status enum
        status_map = {
            PaymentStatus.PENDING: payment_pb2.PENDING,
            PaymentStatus.PROCESSING: payment_pb2.PROCESSING,
            PaymentStatus.COMPLETED: payment_pb2.COMPLETED,
            PaymentStatus.FAILED: payment_pb2.FAILED,
            PaymentStatus.CANCELLED: payment_pb2.CANCELLED,
            PaymentStatus.REFUNDED: payment_pb2.REFUNDED,
        }
        
        # Convert method enum
        method_map = {
            PaymentMethod.CREDIT_CARD: payment_pb2.CREDIT_CARD,
            PaymentMethod.DEBIT_CARD: payment_pb2.DEBIT_CARD,
            PaymentMethod.PAYPAL: payment_pb2.PAYPAL,
            PaymentMethod.STRIPE: payment_pb2.STRIPE,
            PaymentMethod.BANK_TRANSFER: payment_pb2.BANK_TRANSFER,
            PaymentMethod.CASH_ON_DELIVERY: payment_pb2.CASH_ON_DELIVERY,
        }
        
        return payment_pb2.Payment(
            id=payment.id,
            payment_id=payment.payment_id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            method=method_map.get(payment.method, payment_pb2.CREDIT_CARD),
            status=status_map.get(payment.status, payment_pb2.PENDING),
            gateway_payment_id=payment.gateway_payment_id or "",
            card_last_four=payment.card_last_four or "",
            card_brand=payment.card_brand or "",
            failure_reason=payment.failure_reason or "",
            failure_code=payment.failure_code or "",
            created_at=int(payment.created_at.timestamp()) if payment.created_at else 0,
            processed_at=int(payment.processed_at.timestamp()) if payment.processed_at else 0
        )
    
    async def process_stripe_payment(self, amount: int, currency: str, token: str, description: str) -> dict:
        """Process payment via Stripe"""
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency.lower(),
                source=token,
                description=description
            )
            
            return {
                "success": True,
                "gateway_payment_id": charge.id,
                "status": "completed" if charge.paid else "failed",
                "card_last_four": charge.source.last4 if charge.source else None,
                "card_brand": charge.source.brand if charge.source else None,
                "response": charge
            }
            
        except stripe.error.CardError as e:
            return {
                "success": False,
                "failure_reason": str(e),
                "failure_code": e.code,
                "response": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "failure_reason": str(e),
                "failure_code": "processing_error",
                "response": str(e)
            }
    
    async def create_payment(self, db: AsyncSession, request: payment_pb2.CreatePaymentRequest) -> payment_pb2.CreatePaymentResponse:
        """Create and process a payment"""
        try:
            payment_id = self._generate_payment_id()
            
            # Convert protobuf enums to SQLAlchemy enums
            method_map = {
                payment_pb2.CREDIT_CARD: PaymentMethod.CREDIT_CARD,
                payment_pb2.DEBIT_CARD: PaymentMethod.DEBIT_CARD,
                payment_pb2.PAYPAL: PaymentMethod.PAYPAL,
                payment_pb2.STRIPE: PaymentMethod.STRIPE,
                payment_pb2.BANK_TRANSFER: PaymentMethod.BANK_TRANSFER,
                payment_pb2.CASH_ON_DELIVERY: PaymentMethod.CASH_ON_DELIVERY,
            }
            
            payment_method = method_map.get(request.method, PaymentMethod.CREDIT_CARD)
            
            # Create payment record
            payment = Payment(
                payment_id=payment_id,
                order_id=request.order_id,
                user_id=request.user_id,
                amount=request.amount,
                currency=request.currency,
                method=payment_method,
                status=PaymentStatus.PROCESSING
            )
            
            db.add(payment)
            await db.flush()  # Get payment ID
            
            # Process payment based on method
            if payment_method == PaymentMethod.STRIPE:
                result = await self.process_stripe_payment(
                    amount=request.amount,
                    currency=request.currency,
                    token=request.payment_token,
                    description=f"Order #{request.order_id}"
                )
                
                if result["success"]:
                    payment.status = PaymentStatus.COMPLETED
                    payment.gateway_payment_id = result["gateway_payment_id"]
                    payment.card_last_four = result.get("card_last_four")
                    payment.card_brand = result.get("card_brand")
                    payment.processed_at = datetime.utcnow()
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.failure_reason = result["failure_reason"]
                    payment.failure_code = result["failure_code"]
                
                payment.gateway_response = json.dumps(result["response"], default=str)
                
            elif payment_method == PaymentMethod.CASH_ON_DELIVERY:
                payment.status = PaymentStatus.PENDING
                # COD payments are completed upon delivery
                
            else:
                # For other payment methods, mark as pending for manual processing
                payment.status = PaymentStatus.PENDING
            
            await db.commit()
            
            return payment_pb2.CreatePaymentResponse(
                success=True,
                payment=self._convert_payment_to_proto(payment),
                message="Payment processed successfully" if payment.status == PaymentStatus.COMPLETED else "Payment created"
            )
            
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            await db.rollback()
            return payment_pb2.CreatePaymentResponse(
                success=False,
                message="Failed to process payment"
            )
    
    async def get_payment(self, db: AsyncSession, request: payment_pb2.GetPaymentRequest) -> payment_pb2.GetPaymentResponse:
        """Get payment by ID"""
        try:
            result = await db.execute(
                select(Payment).where(Payment.payment_id == request.payment_id)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                return payment_pb2.GetPaymentResponse(
                    success=False,
                    message="Payment not found"
                )
            
            return payment_pb2.GetPaymentResponse(
                success=True,
                payment=self._convert_payment_to_proto(payment)
            )
            
        except Exception as e:
            logger.error(f"Error getting payment: {e}")
            return payment_pb2.GetPaymentResponse(
                success=False,
                message="Failed to get payment"
            )
    
    async def get_order_payments(self, db: AsyncSession, request: payment_pb2.GetOrderPaymentsRequest) -> payment_pb2.GetOrderPaymentsResponse:
        """Get all payments for an order"""
        try:
            result = await db.execute(
                select(Payment).where(Payment.order_id == request.order_id)
            )
            payments = result.scalars().all()
            
            payment_list = [self._convert_payment_to_proto(payment) for payment in payments]
            
            return payment_pb2.GetOrderPaymentsResponse(
                success=True,
                payments=payment_list
            )
            
        except Exception as e:
            logger.error(f"Error getting order payments: {e}")
            return payment_pb2.GetOrderPaymentsResponse(
                success=False,
                message="Failed to get order payments"
            )
    
    async def refund_payment(self, db: AsyncSession, request: payment_pb2.RefundPaymentRequest) -> payment_pb2.RefundPaymentResponse:
        """Process a refund"""
        try:
            # Get original payment
            result = await db.execute(
                select(Payment).where(Payment.payment_id == request.payment_id)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                return payment_pb2.RefundPaymentResponse(
                    success=False,
                    message="Payment not found"
                )
            
            if payment.status != PaymentStatus.COMPLETED:
                return payment_pb2.RefundPaymentResponse(
                    success=False,
                    message="Can only refund completed payments"
                )
            
            refund_id = self._generate_refund_id()
            refund_amount = request.amount if request.amount > 0 else payment.amount
            
            # Create refund record
            refund = Refund(
                refund_id=refund_id,
                payment_id=payment.id,
                order_id=payment.order_id,
                amount=refund_amount,
                reason=request.reason,
                status=PaymentStatus.PROCESSING
            )
            
            db.add(refund)
            await db.flush()
            
            # Process refund via payment gateway
            if payment.method == PaymentMethod.STRIPE and payment.gateway_payment_id:
                try:
                    stripe_refund = stripe.Refund.create(
                        charge=payment.gateway_payment_id,
                        amount=refund_amount
                    )
                    
                    refund.status = PaymentStatus.COMPLETED
                    refund.gateway_refund_id = stripe_refund.id
                    refund.gateway_response = json.dumps(stripe_refund, default=str)
                    refund.processed_at = datetime.utcnow()
                    
                    # Update original payment status if fully refunded
                    if refund_amount >= payment.amount:
                        payment.status = PaymentStatus.REFUNDED
                    
                except Exception as e:
                    refund.status = PaymentStatus.FAILED
                    refund.gateway_response = str(e)
            else:
                # Mark as pending for manual processing
                refund.status = PaymentStatus.PENDING
            
            await db.commit()
            
            return payment_pb2.RefundPaymentResponse(
                success=True,
                refund_id=refund_id,
                message="Refund processed successfully" if refund.status == PaymentStatus.COMPLETED else "Refund created"
            )
            
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            await db.rollback()
            return payment_pb2.RefundPaymentResponse(
                success=False,
                message="Failed to process refund"
            )
