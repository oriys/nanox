from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.clients import grpc_clients
from app.middleware import get_optional_user_id
from app.proto import product_pb2
import grpc

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int  # Price in cents
    category_id: int
    category_name: str
    sku: str
    stock_quantity: int
    images: List[str]
    is_active: bool
    created_at: int

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    parent_id: Optional[int]
    is_active: bool

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    user_id: Optional[int] = Depends(get_optional_user_id)
):
    """Get products with pagination and filtering"""
    try:
        grpc_request = product_pb2.GetProductsRequest(
            page=page,
            page_size=page_size,
            category_id=category_id or 0,
            search_query=search or ""
        )
        
        response = await grpc_clients.product_stub.GetProducts(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        products = []
        for product in response.products:
            products.append(ProductResponse(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                category_id=product.category_id,
                category_name=product.category_name,
                sku=product.sku,
                stock_quantity=product.stock_quantity,
                images=list(product.images),
                is_active=product.is_active,
                created_at=product.created_at
            ))
        
        return products
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, user_id: Optional[int] = Depends(get_optional_user_id)):
    """Get product by ID"""
    try:
        grpc_request = product_pb2.GetProductRequest(product_id=product_id)
        response = await grpc_clients.product_stub.GetProduct(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)
        
        product = response.product
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            category_id=product.category_id,
            category_name=product.category_name,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            images=list(product.images),
            is_active=product.is_active,
            created_at=product.created_at
        )
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.get("/categories/", response_model=List[CategoryResponse])
async def get_categories():
    """Get all product categories"""
    try:
        grpc_request = product_pb2.GetCategoriesRequest()
        response = await grpc_clients.product_stub.GetCategories(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        categories = []
        for category in response.categories:
            categories.append(CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_id=category.parent_id if category.parent_id > 0 else None,
                is_active=category.is_active
            ))
        
        return categories
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")
