#!/bin/bash

# 激活虚拟环境
source ../../venv/bin/activate

# 生成所有服务的gRPC文件
SERVICES=("user-service" "product-service" "cart-service" "order-service" "payment-service" "store-service")
PROTOS=("user" "product" "cart" "order" "payment" "store")

echo "Generating gRPC files for all services..."

for i in "${!SERVICES[@]}"; do
    SERVICE=${SERVICES[$i]}
    PROTO=${PROTOS[$i]}
    
    echo "Generating gRPC files for $SERVICE..."
    
    # 创建目录
    mkdir -p "../$SERVICE/app/proto"
    
    # 生成gRPC文件
    cd "../$SERVICE"
    python -m grpc_tools.protoc \
        -I../../shared/proto \
        --python_out=app/proto \
        --grpc_python_out=app/proto \
        "../../shared/proto/$PROTO.proto"
    
    # 创建__init__.py
    echo "# 导入生成的gRPC文件
from .${PROTO}_pb2 import *
from .${PROTO}_pb2_grpc import *" > "app/proto/__init__.py"
    
    cd ../user-service
done

echo "gRPC files generation completed!"
