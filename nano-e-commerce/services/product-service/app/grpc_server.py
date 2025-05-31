import grpc
from app.proto import product_pb2_grpc, product_pb2
from app.service import ProductService, CategoryService
import logging

logger = logging.getLogger(__name__)

class ProductServicer(product_pb2_grpc.ProductServiceServicer):
    """商品服务gRPC实现"""
    
    def __init__(self):
        self.product_service = ProductService()
        self.category_service = CategoryService()
    
    async def CreateProduct(self, request, context):
        """创建商品"""
        try:
            success, message, product = await self.product_service.create_product(
                name=request.name,
                description=request.description,
                images=list(request.images),
                price=request.price,
                category_id=request.category_id,
                store_id=request.store_id,
                stock=request.stock,
                attributes=dict(request.attributes) if request.attributes else {}
            )
            
            response = product_pb2.CreateProductResponse()
            response.success = success
            response.message = message
            
            if success and product:
                self._fill_product_response(response.product, product)
            
            return response
            
        except Exception as e:
            logger.error(f"CreateProduct error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.CreateProductResponse()
    
    async def GetProduct(self, request, context):
        """获取商品详情"""
        try:
            success, message, product = await self.product_service.get_product_by_id(request.product_id)
            
            response = product_pb2.GetProductResponse()
            response.success = success
            response.message = message
            
            if success and product:
                self._fill_product_response(response.product, product)
            
            return response
            
        except Exception as e:
            logger.error(f"GetProduct error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.GetProductResponse()
    
    async def UpdateProduct(self, request, context):
        """更新商品"""
        try:
            success, message, product = await self.product_service.update_product(
                product_id=request.product_id,
                name=request.name if request.name else None,
                description=request.description if request.description else None,
                images=list(request.images) if request.images else None,
                price=request.price if request.price else None,
                category_id=request.category_id if request.category_id else None,
                stock=request.stock if request.HasField('stock') else None,
                status=request.status if request.status else None,
                attributes=dict(request.attributes) if request.attributes else None
            )
            
            response = product_pb2.UpdateProductResponse()
            response.success = success
            response.message = message
            
            if success and product:
                self._fill_product_response(response.product, product)
            
            return response
            
        except Exception as e:
            logger.error(f"UpdateProduct error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.UpdateProductResponse()
    
    async def DeleteProduct(self, request, context):
        """删除商品"""
        try:
            success, message = await self.product_service.delete_product(
                product_id=request.product_id,
                store_id=request.store_id
            )
            
            response = product_pb2.DeleteProductResponse()
            response.success = success
            response.message = message
            
            return response
            
        except Exception as e:
            logger.error(f"DeleteProduct error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.DeleteProductResponse()
    
    async def ListProducts(self, request, context):
        """获取商品列表"""
        try:
            success, message, products, total = await self.product_service.list_products(
                page=request.page if request.page > 0 else 1,
                page_size=request.page_size if request.page_size > 0 else 20,
                category_id=request.category_id if request.category_id > 0 else None,
                store_id=request.store_id if request.store_id > 0 else None,
                status=request.status if request.status else None,
                sort_by=request.sort_by if request.sort_by else "created_at",
                sort_order=request.sort_order if request.sort_order else "desc"
            )
            
            response = product_pb2.ListProductsResponse()
            response.success = success
            response.message = message
            response.total = total
            response.page = request.page if request.page > 0 else 1
            response.page_size = request.page_size if request.page_size > 0 else 20
            
            if success:
                for product in products:
                    product_pb = response.products.add()
                    self._fill_product_response(product_pb, product)
            
            return response
            
        except Exception as e:
            logger.error(f"ListProducts error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.ListProductsResponse()
    
    async def SearchProducts(self, request, context):
        """搜索商品"""
        try:
            success, message, products, total = await self.product_service.search_products(
                keyword=request.keyword,
                page=request.page if request.page > 0 else 1,
                page_size=request.page_size if request.page_size > 0 else 20,
                category_id=request.category_id if request.category_id > 0 else None,
                min_price=request.min_price if request.min_price > 0 else None,
                max_price=request.max_price if request.max_price > 0 else None,
                sort_by=request.sort_by if request.sort_by else "created_at",
                sort_order=request.sort_order if request.sort_order else "desc"
            )
            
            response = product_pb2.SearchProductsResponse()
            response.success = success
            response.message = message
            response.total = total
            response.page = request.page if request.page > 0 else 1
            response.page_size = request.page_size if request.page_size > 0 else 20
            
            if success:
                for product in products:
                    product_pb = response.products.add()
                    self._fill_product_response(product_pb, product)
            
            return response
            
        except Exception as e:
            logger.error(f"SearchProducts error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.SearchProductsResponse()
    
    async def CreateCategory(self, request, context):
        """创建分类"""
        try:
            success, message, category = await self.category_service.create_category(
                name=request.name,
                description=request.description if request.description else None,
                parent_id=request.parent_id if request.parent_id > 0 else None,
                image=request.image if request.image else None,
                sort_order=request.sort_order
            )
            
            response = product_pb2.CreateCategoryResponse()
            response.success = success
            response.message = message
            
            if success and category:
                self._fill_category_response(response.category, category)
            
            return response
            
        except Exception as e:
            logger.error(f"CreateCategory error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.CreateCategoryResponse()
    
    async def GetCategories(self, request, context):
        """获取分类列表"""
        try:
            success, message, categories = await self.category_service.get_categories(
                parent_id=request.parent_id
            )
            
            response = product_pb2.GetCategoriesResponse()
            response.success = success
            response.message = message
            
            if success:
                for category in categories:
                    category_pb = response.categories.add()
                    self._fill_category_response(category_pb, category)
            
            return response
            
        except Exception as e:
            logger.error(f"GetCategories error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.GetCategoriesResponse()
    
    async def UpdateCategory(self, request, context):
        """更新分类"""
        try:
            success, message, category = await self.category_service.update_category(
                category_id=request.category_id,
                name=request.name if request.name else None,
                description=request.description if request.description else None,
                image=request.image if request.image else None,
                sort_order=request.sort_order if request.HasField('sort_order') else None,
                status=request.status if request.status else None
            )
            
            response = product_pb2.UpdateCategoryResponse()
            response.success = success
            response.message = message
            
            if success and category:
                self._fill_category_response(response.category, category)
            
            return response
            
        except Exception as e:
            logger.error(f"UpdateCategory error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.UpdateCategoryResponse()
    
    async def DeleteCategory(self, request, context):
        """删除分类"""
        try:
            success, message = await self.category_service.delete_category(request.category_id)
            
            response = product_pb2.DeleteCategoryResponse()
            response.success = success
            response.message = message
            
            return response
            
        except Exception as e:
            logger.error(f"DeleteCategory error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.DeleteCategoryResponse()
    
    async def UpdateStock(self, request, context):
        """更新库存"""
        try:
            success, message, current_stock = await self.product_service.update_stock(
                product_id=request.product_id,
                quantity=request.quantity,
                reason=request.reason
            )
            
            response = product_pb2.UpdateStockResponse()
            response.success = success
            response.message = message
            response.current_stock = current_stock
            
            return response
            
        except Exception as e:
            logger.error(f"UpdateStock error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.UpdateStockResponse()
    
    async def CheckStock(self, request, context):
        """检查库存"""
        try:
            available, current_stock, message = await self.product_service.check_stock(
                product_id=request.product_id,
                quantity=request.quantity
            )
            
            response = product_pb2.CheckStockResponse()
            response.available = available
            response.current_stock = current_stock
            response.message = message
            
            return response
            
        except Exception as e:
            logger.error(f"CheckStock error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.CheckStockResponse()
    
    async def ReserveStock(self, request, context):
        """预留库存"""
        try:
            success, message, reservation_id = await self.product_service.reserve_stock(
                product_id=request.product_id,
                quantity=request.quantity,
                order_id=request.order_id
            )
            
            response = product_pb2.ReserveStockResponse()
            response.success = success
            response.message = message
            if reservation_id:
                response.reservation_id = reservation_id
            
            return response
            
        except Exception as e:
            logger.error(f"ReserveStock error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.ReserveStockResponse()
    
    async def ReleaseStock(self, request, context):
        """释放库存"""
        try:
            success, message = await self.product_service.release_stock(request.reservation_id)
            
            response = product_pb2.ReleaseStockResponse()
            response.success = success
            response.message = message
            
            return response
            
        except Exception as e:
            logger.error(f"ReleaseStock error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return product_pb2.ReleaseStockResponse()
    
    def _fill_product_response(self, product_pb, product):
        """填充商品响应数据"""
        product_pb.id = product.id
        product_pb.name = product.name
        product_pb.description = product.description or ""
        product_pb.images.extend(product.images or [])
        product_pb.price = product.price
        product_pb.category_id = product.category_id
        product_pb.store_id = product.store_id
        product_pb.stock = product.stock
        product_pb.status = product.status
        if product.attributes:
            for key, value in product.attributes.items():
                product_pb.attributes[key] = value
        product_pb.created_at = product.created_at
        product_pb.updated_at = product.updated_at
    
    def _fill_category_response(self, category_pb, category):
        """填充分类响应数据"""
        category_pb.id = category.id
        category_pb.name = category.name
        category_pb.description = category.description or ""
        category_pb.parent_id = category.parent_id or 0
        category_pb.image = category.image or ""
        category_pb.sort_order = category.sort_order
        category_pb.status = category.status
        category_pb.created_at = category.created_at
        category_pb.updated_at = category.updated_at
