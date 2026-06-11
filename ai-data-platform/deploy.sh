#!/bin/bash
# AI数据分析平台 - 阿里云服务器部署脚本
# 请在阿里云控制台VNC登录服务器后执行此脚本

set -e

echo "========================================"
echo "  AI数据分析平台 - 自动部署脚本"
echo "========================================"

# 更新系统
echo "[1/8] 更新系统..."
apt-get update -y && apt-get upgrade -y

# 安装基础依赖
echo "[2/8] 安装基础依赖..."
apt-get install -y curl wget git python3 python3-pip python3-venv nodejs npm nginx

# 安装Node.js 20
echo "[3/8] 安装Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# 创建工作目录
echo "[4/8] 创建工作目录..."
mkdir -p /opt/ai-data-platform

# 克隆代码（假设代码已打包上传）
# 实际部署时，需要将代码上传到服务器

echo "[5/8] 配置Nginx..."
cat > /etc/nginx/sites-available/ai-data-platform << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8788;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ai-data-platform /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "[6/8] 配置系统服务..."

# 后端服务
cat > /etc/systemd/system/ai-data-backend.service << 'EOF'
[Unit]
Description=AI Data Platform Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-data-platform/backend
ExecStart=/opt/ai-data-platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8787
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 前端服务
cat > /etc/systemd/system/ai-data-frontend.service << 'EOF'
[Unit]
Description=AI Data Platform Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-data-platform/frontend
ExecStart=/usr/bin/npm run start -- --port 8788
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "[7/8] 配置防火墙..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8787/tcp
ufw allow 8788/tcp
ufw --force enable

echo "[8/8] 部署完成！"
echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "请将项目代码上传到 /opt/ai-data-platform/ 目录后执行："
echo "  cd /opt/ai-data-platform/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "  cd /opt/ai-data-platform/frontend && npm install && npm run build"
echo ""
echo "然后启动服务："
echo "  systemctl start ai-data-backend"
echo "  systemctl start ai-data-frontend"
echo ""
echo "访问地址：http://47.112.170.125"
echo ""
echo "========================================"
