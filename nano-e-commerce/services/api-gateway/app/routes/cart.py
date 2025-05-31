from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.clients import grpc_clients
from app.middleware import get_current_user_id
from app.proto import cart_pb2
import grpc

router = APIRouter(prefix="/api/v1/cart", tags=["Shopping Cart"])

class AddItemRequest(BaseModel):
    product_id: int
    quantity: int

class UpdateItemRequest(BaseModel):
    product_id: int
    quantity: int
    selected: bool = True

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: str
    quantity: int
    price: int  # Price in cents
    selected: bool

class CartResponse(BaseModel):
    user_id: int
    items: List[CartItemResponse]
    total_count: int
    total_amount: int  # Total in cents
    total_selected_count: int

@router.post("/items")
async def add_item_to_cart(request: AddItemRequest, user_id: int = Depends(get_current_user_id)):
    """Add item to cart"""
    try:
        grpc_request = cart_pb2.AddItemRequest(
            user_id=user_id,
            product_id=request.product_id,
            quantity=request.quantity
        )
        
        response = await grpc_clients.cart_stub.AddItem(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return {"message": response.message}
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.put("/items")
async def update_cart_item(request: UpdateItemRequest, user_id: int = Depends(get_current_user_id)):
    """Update cart item"""
    try:
        grpc_request = cart_pb2.UpdateItemRequest(
            user_id=user_id,
            product_id=request.product_id,
            quantity=request.quantity,
            selected=request.selected
        )
        
        response = await grpc_clients.cart_stub.UpdateItem(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return {"message": response.message}
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.delete("/items/{product_id}")
async def remove_item_from_cart(product_id: int, user_id: int = Depends(get_current_user_id)):
    """Remove item from cart"""
    try:
        grpc_request = cart_pb2.RemoveItemRequest(
            user_id=user_id,
            product_id=product_id
        )
        
        response = await grpc_clients.cart_stub.RemoveItem(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return {"message": response.message}
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.get("/", response_model=CartResponse)
async def get_cart(user_id: int = Depends(get_current_user_id)):
    """Get user's cart"""
    try:
        grpc_request = cart_pb2.GetCartRequest(user_id=user_id)
        response = await grpc_clients.cart_stub.GetCart(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        cart = response.cart
        items = []
        for item in cart.items:
            items.append(CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_image=item.product_image,
                quantity=item.quantity,
                price=item.price,
                selected=item.selected
            ))
        
        return CartResponse(
            user_id=cart.user_id,
            items=items,
            total_count=cart.total_count,
            total_amount=cart.total_amount,
            total_selected_count=cart.total_selected_count
        )
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.delete("/")
async def clear_cart(user_id: int = Depends(get_current_user_id)):
    """Clear user's cart"""
    try:
        grpc_request = cart_pb2.ClearCartRequest(user_id=user_id)
        response = await grpc_clients.cart_stub.ClearCart(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return {"message": response.message}
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.get("/count")
async def get_cart_count(user_id: int = Depends(get_current_user_id)):
    """Get cart item count"""
    try:
        grpc_request = cart_pb2.GetCartCountRequest(user_id=user_id)
        response = await grpc_clients.cart_stub.GetCartCount(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return {"count": response.count}
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")
