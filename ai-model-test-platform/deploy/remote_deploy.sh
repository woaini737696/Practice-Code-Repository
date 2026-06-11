#!/bin/bash
# 在阿里云服务器上执行的完整部署脚本
set -e

echo "=========================================="
echo "AI模型测试平台 - 远程部署"
echo "=========================================="

# 1. 安装Docker
echo "[1/5] 安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 2. 创建项目目录
echo "[2/5] 创建项目目录..."
PROJECT_DIR="/opt/ai-model-test-platform"
rm -rf $PROJECT_DIR
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 3. 下载项目代码（从临时下载链接或GitHub）
echo "[3/5] 下载项目代码..."
# 方式1: 如果有GitHub仓库
# git clone https://github.com/your-repo/ai-model-test-platform.git .

# 方式2: 从临时HTTP服务器下载（需要先将代码上传到可下载的位置）
# curl -o code.tar.gz http://your-server/code.tar.gz
# tar -xzf code.tar.gz

# 方式3: 直接在服务器上创建所有文件（最可靠）
echo "创建项目文件..."

# 后端 requirements.txt
cat > backend/requirements.txt << 'EOF'
fastapi
uvicorn[standard]
sqlalchemy
alembic
pymysql
cryptography
redis
celery
python-socketio
python-multipart
pydantic
pydantic-settings
httpx
openpyxl
reportlab
aiosmtplib
python-jose[cryptography]
passlib[bcrypt]
openai
jinja2
EOF

# 后端 main.py
cat > backend/main.py << 'EOF'
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import distillation, models, tests, scoring, settings, auth
from app.websocket.manager import websocket_manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Model Test Platform", description="AI聊天模型测试平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(distillation.router)
app.include_router(models.router)
app.include_router(tests.router)
app.include_router(scoring.router)
app.include_router(settings.router)

@app.get("/")
def root():
    return {"message": "AI Model Test Platform API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# 创建目录结构
mkdir -p backend/app/{api,core,models,schemas,services,tasks,websocket}
mkdir -p frontend/src/{pages/{auth,tests,models,distillation,scoring,settings},services}
mkdir -p frontend/public

echo "基础文件创建完成"

# 4. 创建Docker配置
echo "[4/5] 创建Docker配置..."

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

# 前端nginx.conf
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

# 前端package.json
cat > frontend/package.json << 'EOF'
{
  "name": "ai-model-test-platform-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@types/node": "^16.18.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "antd": "^5.12.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.5"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
EOF

# docker-compose.prod.yml
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

echo "Docker配置创建完成"

# 5. 构建并启动
echo "[5/5] 构建并启动服务..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

echo "等待服务启动..."
sleep 15

echo "服务状态:"
docker-compose -f docker-compose.prod.yml ps

# 6. 配置Nginx
echo "配置Nginx..."
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
echo "服务端口（已隔离）:"
echo "  - Web访问: 80 (Nginx)"
echo "  - 前端: 13000"
echo "  - 后端API: 18000"
echo "  - MySQL: 13306"
echo "  - Redis: 16379"
echo ""
echo "默认账号: admin"
echo "默认密码: admin123"
echo "=========================================="
