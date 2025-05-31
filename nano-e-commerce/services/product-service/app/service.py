import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Product, Category, StockReservation
from app.database import SessionLocal

class ProductService:
    """商品服务业务逻辑"""
    
    async def create_product(self, name: str, description: str, images: List[str], 
                           price: int, category_id: int, store_id: int, 
                           stock: int, attributes: Dict[str, str] = None) -> tuple[bool, str, Optional[Product]]:
        """创建商品"""
        async with SessionLocal() as session:
            try:
                # 验证分类存在
                result = await session.execute(
                    select(Category).where(Category.id == category_id, Category.status == "active")
                )
                if not result.scalar_one_or_none():
                    return False, "分类不存在或已禁用", None
                
                # 创建新商品
                new_product = Product(
                    name=name,
                    description=description,
                    images=images,
                    price=price,
                    category_id=category_id,
                    store_id=store_id,
                    stock=stock,
                    attributes=attributes or {}
                )
                
                session.add(new_product)
                await session.commit()
                await session.refresh(new_product)
                
                return True, "商品创建成功", new_product
                
            except Exception as e:
                await session.rollback()
                return False, f"创建失败: {str(e)}", None
    
    async def get_product_by_id(self, product_id: int) -> tuple[bool, str, Optional[Product]]:
        """根据ID获取商品"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Product)
                    .options(selectinload(Product.category))
                    .where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False, "商品不存在", None
                
                return True, "获取成功", product
                
            except Exception as e:
                return False, f"获取失败: {str(e)}", None
    
    async def update_product(self, product_id: int, name: str = None, description: str = None,
                           images: List[str] = None, price: int = None, category_id: int = None,
                           stock: int = None, status: str = None, 
                           attributes: Dict[str, str] = None) -> tuple[bool, str, Optional[Product]]:
        """更新商品"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False, "商品不存在", None
                
                # 如果更新分类，验证分类存在
                if category_id:
                    result = await session.execute(
                        select(Category).where(Category.id == category_id, Category.status == "active")
                    )
                    if not result.scalar_one_or_none():
                        return False, "分类不存在或已禁用", None
                
                # 更新字段
                if name: product.name = name
                if description: product.description = description
                if images is not None: product.images = images
                if price: product.price = price
                if category_id: product.category_id = category_id
                if stock is not None: product.stock = stock
                if status: product.status = status
                if attributes is not None: product.attributes = attributes
                
                await session.commit()
                await session.refresh(product)
                
                return True, "更新成功", product
                
            except Exception as e:
                await session.rollback()
                return False, f"更新失败: {str(e)}", None
    
    async def delete_product(self, product_id: int, store_id: int) -> tuple[bool, str]:
        """删除商品（软删除）"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Product).where(Product.id == product_id, Product.store_id == store_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False, "商品不存在或无权限"
                
                product.status = "deleted"
                await session.commit()
                
                return True, "删除成功"
                
            except Exception as e:
                await session.rollback()
                return False, f"删除失败: {str(e)}"
    
    async def list_products(self, page: int = 1, page_size: int = 20, category_id: int = None,
                          store_id: int = None, status: str = None, sort_by: str = "created_at",
                          sort_order: str = "desc") -> tuple[bool, str, List[Product], int]:
        """获取商品列表"""
        async with SessionLocal() as session:
            try:
                # 构建查询条件
                conditions = []
                if category_id:
                    conditions.append(Product.category_id == category_id)
                if store_id:
                    conditions.append(Product.store_id == store_id)
                if status:
                    conditions.append(Product.status == status)
                else:
                    conditions.append(Product.status != "deleted")
                
                # 构建排序
                sort_column = getattr(Product, sort_by, Product.created_at)
                if sort_order == "asc":
                    order_by = asc(sort_column)
                else:
                    order_by = desc(sort_column)
                
                # 查询总数
                count_query = select(func.count(Product.id)).where(and_(*conditions))
                total_result = await session.execute(count_query)
                total = total_result.scalar()
                
                # 分页查询
                offset = (page - 1) * page_size
                query = (
                    select(Product)
                    .options(selectinload(Product.category))
                    .where(and_(*conditions))
                    .order_by(order_by)
                    .offset(offset)
                    .limit(page_size)
                )
                
                result = await session.execute(query)
                products = result.scalars().all()
                
                return True, "获取成功", list(products), total
                
            except Exception as e:
                return False, f"获取失败: {str(e)}", [], 0
    
    async def search_products(self, keyword: str, page: int = 1, page_size: int = 20,
                            category_id: int = None, min_price: int = None, max_price: int = None,
                            sort_by: str = "created_at", sort_order: str = "desc") -> tuple[bool, str, List[Product], int]:
        """搜索商品"""
        async with SessionLocal() as session:
            try:
                # 构建查询条件
                conditions = [Product.status != "deleted"]
                
                # 关键词搜索
                if keyword:
                    keyword_condition = or_(
                        Product.name.ilike(f"%{keyword}%"),
                        Product.description.ilike(f"%{keyword}%")
                    )
                    conditions.append(keyword_condition)
                
                if category_id:
                    conditions.append(Product.category_id == category_id)
                if min_price is not None:
                    conditions.append(Product.price >= min_price)
                if max_price is not None:
                    conditions.append(Product.price <= max_price)
                
                # 构建排序
                sort_column = getattr(Product, sort_by, Product.created_at)
                if sort_order == "asc":
                    order_by = asc(sort_column)
                else:
                    order_by = desc(sort_column)
                
                # 查询总数
                count_query = select(func.count(Product.id)).where(and_(*conditions))
                total_result = await session.execute(count_query)
                total = total_result.scalar()
                
                # 分页查询
                offset = (page - 1) * page_size
                query = (
                    select(Product)
                    .options(selectinload(Product.category))
                    .where(and_(*conditions))
                    .order_by(order_by)
                    .offset(offset)
                    .limit(page_size)
                )
                
                result = await session.execute(query)
                products = result.scalars().all()
                
                return True, "搜索成功", list(products), total
                
            except Exception as e:
                return False, f"搜索失败: {str(e)}", [], 0
    
    async def update_stock(self, product_id: int, quantity: int, reason: str = "") -> tuple[bool, str, int]:
        """更新库存"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False, "商品不存在", 0
                
                new_stock = product.stock + quantity
                if new_stock < 0:
                    return False, "库存不足", product.stock
                
                product.stock = new_stock
                await session.commit()
                
                return True, f"库存更新成功，原因: {reason}", new_stock
                
            except Exception as e:
                await session.rollback()
                return False, f"更新失败: {str(e)}", 0
    
    async def check_stock(self, product_id: int, quantity: int) -> tuple[bool, int, str]:
        """检查库存"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False, 0, "商品不存在"
                
                if product.stock >= quantity:
                    return True, product.stock, "库存充足"
                else:
                    return False, product.stock, f"库存不足，当前库存: {product.stock}"
                
            except Exception as e:
                return False, 0, f"检查失败: {str(e)}"
    
    async def reserve_stock(self, product_id: int, quantity: int, order_id: str) -> tuple[bool, str, Optional[str]]:
        """预留库存"""
        async with SessionLocal() as session:
            try:
                # 检查商品库存
                result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    return False, "商品不存在", None
                
                if product.stock < quantity:
                    return False, f"库存不足，当前库存: {product.stock}", None
                
                # 创建预留记录
                reservation_id = str(uuid.uuid4())
                expires_at = int((datetime.utcnow() + timedelta(minutes=30)).timestamp())  # 30分钟后过期
                
                reservation = StockReservation(
                    reservation_id=reservation_id,
                    product_id=product_id,
                    quantity=quantity,
                    order_id=order_id,
                    expires_at=expires_at
                )
                
                # 减少可用库存
                product.stock -= quantity
                
                session.add(reservation)
                await session.commit()
                
                return True, "库存预留成功", reservation_id
                
            except Exception as e:
                await session.rollback()
                return False, f"预留失败: {str(e)}", None
    
    async def release_stock(self, reservation_id: str) -> tuple[bool, str]:
        """释放库存预留"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(StockReservation)
                    .options(selectinload(StockReservation.product))
                    .where(StockReservation.reservation_id == reservation_id)
                )
                reservation = result.scalar_one_or_none()
                
                if not reservation:
                    return False, "预留记录不存在"
                
                if reservation.status != "reserved":
                    return False, f"预留状态错误: {reservation.status}"
                
                # 恢复库存
                reservation.product.stock += reservation.quantity
                reservation.status = "released"
                
                await session.commit()
                
                return True, "库存释放成功"
                
            except Exception as e:
                await session.rollback()
                return False, f"释放失败: {str(e)}"

class CategoryService:
    """分类服务业务逻辑"""
    
    async def create_category(self, name: str, description: str = None, parent_id: int = None,
                            image: str = None, sort_order: int = 0) -> tuple[bool, str, Optional[Category]]:
        """创建分类"""
        async with SessionLocal() as session:
            try:
                # 如果有父分类，验证父分类存在
                if parent_id:
                    result = await session.execute(
                        select(Category).where(Category.id == parent_id, Category.status == "active")
                    )
                    if not result.scalar_one_or_none():
                        return False, "父分类不存在或已禁用", None
                
                # 创建新分类
                new_category = Category(
                    name=name,
                    description=description,
                    parent_id=parent_id,
                    image=image,
                    sort_order=sort_order
                )
                
                session.add(new_category)
                await session.commit()
                await session.refresh(new_category)
                
                return True, "分类创建成功", new_category
                
            except Exception as e:
                await session.rollback()
                return False, f"创建失败: {str(e)}", None
    
    async def get_categories(self, parent_id: int = 0) -> tuple[bool, str, List[Category]]:
        """获取分类列表"""
        async with SessionLocal() as session:
            try:
                if parent_id == 0:
                    # 获取根分类
                    query = select(Category).where(
                        Category.parent_id.is_(None),
                        Category.status == "active"
                    ).order_by(Category.sort_order, Category.name)
                else:
                    # 获取子分类
                    query = select(Category).where(
                        Category.parent_id == parent_id,
                        Category.status == "active"
                    ).order_by(Category.sort_order, Category.name)
                
                result = await session.execute(query)
                categories = result.scalars().all()
                
                return True, "获取成功", list(categories)
                
            except Exception as e:
                return False, f"获取失败: {str(e)}", []
    
    async def update_category(self, category_id: int, name: str = None, description: str = None,
                            image: str = None, sort_order: int = None, status: str = None) -> tuple[bool, str, Optional[Category]]:
        """更新分类"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Category).where(Category.id == category_id)
                )
                category = result.scalar_one_or_none()
                
                if not category:
                    return False, "分类不存在", None
                
                # 更新字段
                if name: category.name = name
                if description: category.description = description
                if image: category.image = image
                if sort_order is not None: category.sort_order = sort_order
                if status: category.status = status
                
                await session.commit()
                await session.refresh(category)
                
                return True, "更新成功", category
                
            except Exception as e:
                await session.rollback()
                return False, f"更新失败: {str(e)}", None
    
    async def delete_category(self, category_id: int) -> tuple[bool, str]:
        """删除分类（软删除）"""
        async with SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Category).where(Category.id == category_id)
                )
                category = result.scalar_one_or_none()
                
                if not category:
                    return False, "分类不存在"
                
                # 检查是否有子分类
                result = await session.execute(
                    select(Category).where(Category.parent_id == category_id, Category.status == "active")
                )
                if result.scalars().first():
                    return False, "存在子分类，无法删除"
                
                # 检查是否有关联商品
                result = await session.execute(
                    select(Product).where(Product.category_id == category_id, Product.status != "deleted")
                )
                if result.scalars().first():
                    return False, "存在关联商品，无法删除"
                
                category.status = "inactive"
                await session.commit()
                
                return True, "删除成功"
                
            except Exception as e:
                await session.rollback()
                return False, f"删除失败: {str(e)}"
