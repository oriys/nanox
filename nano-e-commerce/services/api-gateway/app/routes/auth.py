from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.clients import grpc_clients
from app.middleware import get_current_user_id, get_optional_user_id
from app.proto import user_pb2
import grpc

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    created_at: int

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        grpc_request = user_pb2.RegisterRequest(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone or ""
        )
        
        response = await grpc_clients.user_stub.Register(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return TokenResponse(
            access_token=response.token,
            user_id=response.user.id,
            email=response.user.email
        )
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user"""
    try:
        grpc_request = user_pb2.LoginRequest(
            email=request.email,
            password=request.password
        )
        
        response = await grpc_clients.user_stub.Login(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=401, detail=response.message)
        
        return TokenResponse(
            access_token=response.token,
            user_id=response.user.id,
            email=response.user.email
        )
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")

@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """Get current user profile"""
    try:
        grpc_request = user_pb2.GetUserRequest(user_id=user_id)
        response = await grpc_clients.user_stub.GetUser(grpc_request)
        
        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)
        
        user = response.user
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone if user.phone else None,
            created_at=user.created_at
        )
        
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=f"Service unavailable: {e.details()}")
