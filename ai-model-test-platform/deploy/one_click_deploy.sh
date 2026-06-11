#!/bin/bash
# AI模型测试平台 - 阿里云一键部署脚本
# 使用方法：登录阿里云Workbench，复制此脚本到/root目录执行：bash /root/one_click_deploy.sh

set -e

echo "=========================================="
echo "AI模型测试平台 - 一键部署"
echo "=========================================="

PROJECT_DIR="/opt/ai-model-test-platform"
GITHUB_REPO="https://github.com/your-repo/ai-model-test-platform.git"

# 1. 安装Docker和Docker Compose
echo "[1/6] 检查并安装Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "正在安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "正在安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "Docker版本: $(docker --version)"
echo "Docker Compose版本: $(docker-compose --version)"

# 2. 清理旧部署（隔离其他项目）
echo "[2/6] 清理旧部署..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 只清理本项目相关的容器，不影响其他项目
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker ps -aq --filter "name=ai-test-" | xargs -r docker rm -f 2>/dev/null || true
docker network prune -f 2>/dev/null || true

# 3. 从GitHub拉取代码
echo "[3/6] 拉取项目代码..."
if [ -d ".git" ]; then
    git pull
else
    # 如果没有git仓库，创建一个基础结构
    rm -rf backend frontend deploy docker-compose.prod.yml
    mkdir -p backend/app/{api,core,models,schemas,services,tasks,websocket}
    mkdir -p frontend/src/pages/{auth,tests,models,distillation,scoring,settings}
    mkdir -p frontend/src/services frontend/public
fi

# 4. 创建生产环境配置文件
echo "[4/6] 创建配置文件..."

# 后端Dockerfile
cat > backend/Dockerfile.prod << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
EOF

# 前端Dockerfile
cat > frontend/Dockerfile.prod << 'EOF'
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# 前端Nginx配置
cat > frontend/nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /ws {
        proxy_pass http://backend:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Docker Compose配置（使用独立端口，避免冲突）
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: ai-test-mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: AiTest2024!@#
      MYSQL_DATABASE: ai_test
      MYSQL_USER: aitest
      MYSQL_PASSWORD: AiTest2024!@#
    ports:
      - "13306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4
    networks:
      - ai-test-network

  redis:
    image: redis:7-alpine
    container_name: ai-test-redis
    restart: always
    ports:
      - "16379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ai-test-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: ai-test-backend
    restart: always
    ports:
      - "18000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://aitest:AiTest2024!%40%23@mysql:3306/ai_test
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=ai-model-test-platform-secret-key-2024
      - DEBUG=false
    depends_on:
      - mysql
      - redis
    networks:
      - ai-test-network

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: ai-test-celery
    restart: always
    environment:
      - DATABASE_URL=mysql+pymysql://aitest:AiTest2024!%40%23@mysql:3306/ai_test
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=ai-model-test-platform-secret-key-2024
      - DEBUG=false
    depends_on:
      - mysql
      - redis
    command: celery -A app.tasks.celery_app worker --loglevel=info
    networks:
      - ai-test-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: ai-test-frontend
    restart: always
    ports:
      - "13000:80"
    depends_on:
      - backend
    networks:
      - ai-test-network

volumes:
  mysql_data:
  redis_data:

networks:
  ai-test-network:
    driver: bridge
EOF

echo "配置文件创建完成"

# 5. 构建并启动服务
echo "[5/6] 构建并启动Docker服务..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

echo "等待服务启动..."
sleep 15

echo "服务状态:"
docker-compose -f docker-compose.prod.yml ps

# 6. 配置Nginx反向代理
echo "[6/6] 配置Nginx反向代理..."
mkdir -p /etc/nginx/conf.d

cat > /etc/nginx/conf.d/ai-test.conf << 'EOF'
upstream ai_test_backend {
    server 127.0.0.1:18000;
}
upstream ai_test_frontend {
    server 127.0.0.1:13000;
}
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://ai_test_frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://ai_test_backend/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://ai_test_backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://ai_test_backend/health;
    }
}
EOF

nginx -t && systemctl reload nginx

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "访问地址: http://47.112.170.125"
echo ""
echo "服务端口（已隔离，不与其他项目冲突）:"
echo "  - Web访问: 80 (Nginx反向代理)"
echo "  - 前端容器: 13000"
echo "  - 后端API: 18000"
echo "  - MySQL: 13306"
echo "  - Redis: 16379"
echo ""
echo "默认管理员账号: admin"
echo "默认管理员密码: admin123"
echo "=========================================="
