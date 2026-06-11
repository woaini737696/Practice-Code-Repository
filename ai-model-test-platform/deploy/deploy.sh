#!/bin/bash
set -e

echo "=========================================="
echo "AI模型测试平台 - 阿里云部署脚本"
echo "=========================================="

PROJECT_DIR="/opt/ai-model-test-platform"

# 1. 安装Docker和Docker Compose（如未安装）
echo "[1/8] 检查Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "正在安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "正在安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "Docker版本: $(docker --version)"
echo "Docker Compose版本: $(docker-compose --version)"

# 2. 创建项目目录
echo "[2/8] 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 3. 清理旧容器（避免冲突）
echo "[3/8] 清理旧容器..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker ps -aq --filter "name=ai-test-" | xargs -r docker rm -f 2>/dev/null || true

# 4. 拉取最新代码（这里假设代码已通过其他方式上传到服务器）
echo "[4/8] 检查项目文件..."
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "错误: 未找到docker-compose.prod.yml，请先上传项目代码到 $PROJECT_DIR"
    exit 1
fi

# 5. 构建并启动服务
echo "[5/8] 构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "[6/8] 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

# 6. 等待服务启动
echo "[7/8] 等待服务启动..."
sleep 10

# 7. 检查服务状态
echo "[8/8] 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 8. 配置Nginx反向代理
echo "配置Nginx反向代理..."
if [ -f "deploy/nginx-server.conf" ]; then
    cp deploy/nginx-server.conf /etc/nginx/conf.d/ai-test.conf
    nginx -t && systemctl reload nginx
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "访问地址: http://47.112.170.125"
echo "前端端口: 13000"
echo "后端端口: 18000"
echo "MySQL端口: 13306"
echo "Redis端口: 16379"
echo ""
echo "默认管理员账号: admin"
echo "默认管理员密码: admin123"
echo "=========================================="
