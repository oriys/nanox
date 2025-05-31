import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Address
from app.database import SessionLocal

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天

class UserService:
    """用户服务业务逻辑"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(user_id: int) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"user_id": user_id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[int]:
        """验证令牌并返回用户ID"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("user_id")
            if user_id is None:
                return None
            return user_id
        except jwt.PyJWTError:
            return None
    
    async def register_user(self, username: str, email: str, password: str, phone: str = None) -> tuple[bool, str, Optional[User]]:
        """用户注册"""
        async with SessionLocal() as session:
            try:
                # 检查用户名是否已存在
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                if result.scalar_one_or_none():
                    return False, "用户名已存在", None
                
                # 检查邮箱是否已存在
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                if result.scalar_one_or_none():
                    return False, "邮箱已存在", None
                
                # 检查手机号是否已存在（如果提供）
                if phone:
                    result = await session.execute(
                        select(User).where(User.phone == phone)
                    )
                    if result.scalar_one_or_none():
                        return False, "手机号已存在", None
                
                # 创建新用户
                hashed_password = self.hash_password(password)
                new_user = User(
                    username=username,
                    email=email,
                    phone=phone,
                    password_hash=hashed_password
                )
                
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                
                return True, "注册成功", new_user
                
            except Exception as e:
                await session.rollback()
                return False, f"注册失败: {str(e)}", None
    
    async def login_user(self, email: str, password: str) -> tuple[bool, str, Optional[User], Optional[str]]:
        """用户登录"""
        async with SessionLocal() as session:
            try:
                # 查找用户
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False, "用户不存在", None, None
                
                if not user.is_active:
                    return False, "账户已被禁用", None, None
                
                # 验证密码
                if not self.verify_password(password, user.password_hash):
                    return False, "密码错误", None, None
                
                # 创建访问令牌
                token = self.create_access_token(user.id)
                
                return True, "登录成功", user, token
                
            except Exception as e:
                return False, f"登录失败: {str(e)}", None, None
    
    async def get_user_by_id(self, user_id: int) -> tuple[bool, str, Optional[User]]:
        """根据ID获取用户信息"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False, "用户不存在", None
                
                return True, "获取成功", user
                
            except Exception as e:
                return False, f"获取失败: {str(e)}", None
    
    async def update_user(self, user_id: int, username: str = None, phone: str = None, avatar: str = None) -> tuple[bool, str, Optional[User]]:
        """更新用户信息"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False, "用户不存在", None
                
                # 更新字段
                if username:
                    # 检查用户名是否已被其他用户使用
                    result = await session.execute(
                        select(User).where(User.username == username, User.id != user_id)
                    )
                    if result.scalar_one_or_none():
                        return False, "用户名已被使用", None
                    user.username = username
                
                if phone:
                    # 检查手机号是否已被其他用户使用
                    result = await session.execute(
                        select(User).where(User.phone == phone, User.id != user_id)
                    )
                    if result.scalar_one_or_none():
                        return False, "手机号已被使用", None
                    user.phone = phone
                
                if avatar:
                    user.avatar = avatar
                
                await session.commit()
                await session.refresh(user)
                
                return True, "更新成功", user
                
            except Exception as e:
                await session.rollback()
                return False, f"更新失败: {str(e)}", None
    
    async def add_address(self, user_id: int, name: str, phone: str, province: str, 
                         city: str, district: str, detail: str, postal_code: str = None,
                         is_default: bool = False) -> tuple[bool, str, Optional[Address]]:
        """添加地址"""
        async with SessionLocal() as session:
            try:
                # 验证用户存在
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                if not result.scalar_one_or_none():
                    return False, "用户不存在", None
                
                # 如果设置为默认地址，先取消其他默认地址
                if is_default:
                    await session.execute(
                        select(Address).where(Address.user_id == user_id, Address.is_default == True)
                    )
                    result = await session.execute(
                        select(Address).where(Address.user_id == user_id, Address.is_default == True)
                    )
                    for addr in result.scalars():
                        addr.is_default = False
                
                # 创建新地址
                new_address = Address(
                    user_id=user_id,
                    name=name,
                    phone=phone,
                    province=province,
                    city=city,
                    district=district,
                    detail=detail,
                    postal_code=postal_code,
                    is_default=is_default
                )
                
                session.add(new_address)
                await session.commit()
                await session.refresh(new_address)
                
                return True, "添加成功", new_address
                
            except Exception as e:
                await session.rollback()
                return False, f"添加失败: {str(e)}", None
    
    async def get_user_addresses(self, user_id: int) -> tuple[bool, str, list[Address]]:
        """获取用户地址列表"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc(), Address.created_at.desc())
                )
                addresses = result.scalars().all()
                
                return True, "获取成功", list(addresses)
                
            except Exception as e:
                return False, f"获取失败: {str(e)}", []
    
    async def update_address(self, address_id: int, user_id: int, name: str = None, 
                           phone: str = None, province: str = None, city: str = None,
                           district: str = None, detail: str = None, postal_code: str = None,
                           is_default: bool = None) -> tuple[bool, str, Optional[Address]]:
        """更新地址"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Address).where(Address.id == address_id, Address.user_id == user_id)
                )
                address = result.scalar_one_or_none()
                
                if not address:
                    return False, "地址不存在或无权限", None
                
                # 如果设置为默认地址，先取消其他默认地址
                if is_default:
                    result = await session.execute(
                        select(Address).where(Address.user_id == user_id, Address.is_default == True, Address.id != address_id)
                    )
                    for addr in result.scalars():
                        addr.is_default = False
                
                # 更新字段
                if name: address.name = name
                if phone: address.phone = phone
                if province: address.province = province
                if city: address.city = city
                if district: address.district = district
                if detail: address.detail = detail
                if postal_code: address.postal_code = postal_code
                if is_default is not None: address.is_default = is_default
                
                await session.commit()
                await session.refresh(address)
                
                return True, "更新成功", address
                
            except Exception as e:
                await session.rollback()
                return False, f"更新失败: {str(e)}", None
    
    async def delete_address(self, address_id: int, user_id: int) -> tuple[bool, str]:
        """删除地址"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Address).where(Address.id == address_id, Address.user_id == user_id)
                )
                address = result.scalar_one_or_none()
                
                if not address:
                    return False, "地址不存在或无权限"
                
                await session.delete(address)
                await session.commit()
                
                return True, "删除成功"
                
            except Exception as e:
                await session.rollback()
                return False, f"删除失败: {str(e)}"
