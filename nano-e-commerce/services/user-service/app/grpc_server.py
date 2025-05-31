import grpc
from app.proto import user_pb2_grpc, user_pb2
from app.service import UserService
import logging

logger = logging.getLogger(__name__)

class UserServicer(user_pb2_grpc.UserServiceServicer):
    """用户服务gRPC实现"""
    
    def __init__(self):
        self.user_service = UserService()
    
    async def Register(self, request, context):
        """用户注册"""
        try:
            success, message, user = await self.user_service.register_user(
                username=request.username,
                email=request.email,
                password=request.password,
                phone=request.phone if request.phone else None
            )
            
            response = user_pb2.RegisterResponse()
            response.success = success
            response.message = message
            
            if success and user:
                # 创建访问令牌
                token = self.user_service.create_access_token(user.id)
                response.token = token
                
                # 填充用户信息
                response.user.id = user.id
                response.user.username = user.username
                response.user.email = user.email
                response.user.phone = user.phone or ""
                response.user.avatar = user.avatar or ""
                response.user.created_at = user.created_at
                response.user.updated_at = user.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"Register error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.RegisterResponse()
    
    async def Login(self, request, context):
        """用户登录"""
        try:
            success, message, user, token = await self.user_service.login_user(
                email=request.email,
                password=request.password
            )
            
            response = user_pb2.LoginResponse()
            response.success = success
            response.message = message
            
            if success and user and token:
                response.token = token
                
                # 填充用户信息
                response.user.id = user.id
                response.user.username = user.username
                response.user.email = user.email
                response.user.phone = user.phone or ""
                response.user.avatar = user.avatar or ""
                response.user.created_at = user.created_at
                response.user.updated_at = user.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.LoginResponse()
    
    async def GetUser(self, request, context):
        """获取用户信息"""
        try:
            success, message, user = await self.user_service.get_user_by_id(request.user_id)
            
            response = user_pb2.GetUserResponse()
            response.success = success
            response.message = message
            
            if success and user:
                response.user.id = user.id
                response.user.username = user.username
                response.user.email = user.email
                response.user.phone = user.phone or ""
                response.user.avatar = user.avatar or ""
                response.user.created_at = user.created_at
                response.user.updated_at = user.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"GetUser error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.GetUserResponse()
    
    async def UpdateUser(self, request, context):
        """更新用户信息"""
        try:
            success, message, user = await self.user_service.update_user(
                user_id=request.user_id,
                username=request.username if request.username else None,
                phone=request.phone if request.phone else None,
                avatar=request.avatar if request.avatar else None
            )
            
            response = user_pb2.UpdateUserResponse()
            response.success = success
            response.message = message
            
            if success and user:
                response.user.id = user.id
                response.user.username = user.username
                response.user.email = user.email
                response.user.phone = user.phone or ""
                response.user.avatar = user.avatar or ""
                response.user.created_at = user.created_at
                response.user.updated_at = user.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"UpdateUser error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.UpdateUserResponse()
    
    async def ValidateToken(self, request, context):
        """验证Token"""
        try:
            user_id = self.user_service.verify_token(request.token)
            
            response = user_pb2.ValidateTokenResponse()
            
            if user_id:
                response.valid = True
                response.user_id = user_id
                response.message = "令牌有效"
            else:
                response.valid = False
                response.user_id = 0
                response.message = "令牌无效或已过期"
            
            return response
            
        except Exception as e:
            logger.error(f"ValidateToken error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.ValidateTokenResponse()
    
    async def AddAddress(self, request, context):
        """添加地址"""
        try:
            success, message, address = await self.user_service.add_address(
                user_id=request.user_id,
                name=request.name,
                phone=request.phone,
                province=request.province,
                city=request.city,
                district=request.district,
                detail=request.detail,
                postal_code=request.postal_code if request.postal_code else None,
                is_default=request.is_default
            )
            
            response = user_pb2.AddAddressResponse()
            response.success = success
            response.message = message
            
            if success and address:
                response.address.id = address.id
                response.address.user_id = address.user_id
                response.address.name = address.name
                response.address.phone = address.phone
                response.address.province = address.province
                response.address.city = address.city
                response.address.district = address.district
                response.address.detail = address.detail
                response.address.postal_code = address.postal_code or ""
                response.address.is_default = address.is_default
                response.address.created_at = address.created_at
                response.address.updated_at = address.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"AddAddress error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.AddAddressResponse()
    
    async def GetAddresses(self, request, context):
        """获取地址列表"""
        try:
            success, message, addresses = await self.user_service.get_user_addresses(request.user_id)
            
            response = user_pb2.GetAddressesResponse()
            response.success = success
            response.message = message
            
            if success:
                for address in addresses:
                    addr = response.addresses.add()
                    addr.id = address.id
                    addr.user_id = address.user_id
                    addr.name = address.name
                    addr.phone = address.phone
                    addr.province = address.province
                    addr.city = address.city
                    addr.district = address.district
                    addr.detail = address.detail
                    addr.postal_code = address.postal_code or ""
                    addr.is_default = address.is_default
                    addr.created_at = address.created_at
                    addr.updated_at = address.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"GetAddresses error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.GetAddressesResponse()
    
    async def UpdateAddress(self, request, context):
        """更新地址"""
        try:
            success, message, address = await self.user_service.update_address(
                address_id=request.address_id,
                user_id=request.user_id,
                name=request.name if request.name else None,
                phone=request.phone if request.phone else None,
                province=request.province if request.province else None,
                city=request.city if request.city else None,
                district=request.district if request.district else None,
                detail=request.detail if request.detail else None,
                postal_code=request.postal_code if request.postal_code else None,
                is_default=request.is_default if request.HasField('is_default') else None
            )
            
            response = user_pb2.UpdateAddressResponse()
            response.success = success
            response.message = message
            
            if success and address:
                response.address.id = address.id
                response.address.user_id = address.user_id
                response.address.name = address.name
                response.address.phone = address.phone
                response.address.province = address.province
                response.address.city = address.city
                response.address.district = address.district
                response.address.detail = address.detail
                response.address.postal_code = address.postal_code or ""
                response.address.is_default = address.is_default
                response.address.created_at = address.created_at
                response.address.updated_at = address.updated_at
            
            return response
            
        except Exception as e:
            logger.error(f"UpdateAddress error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.UpdateAddressResponse()
    
    async def DeleteAddress(self, request, context):
        """删除地址"""
        try:
            success, message = await self.user_service.delete_address(
                address_id=request.address_id,
                user_id=request.user_id
            )
            
            response = user_pb2.DeleteAddressResponse()
            response.success = success
            response.message = message
            
            return response
            
        except Exception as e:
            logger.error(f"DeleteAddress error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return user_pb2.DeleteAddressResponse()
