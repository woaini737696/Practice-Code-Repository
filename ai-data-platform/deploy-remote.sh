#!/bin/bash
set -e

echo "========================================"
echo "  AI数据分析平台 - 远程部署脚本"
echo "========================================"

# 1. 更新系统并安装依赖
echo "[1/6] 更新系统并安装依赖..."
apt-get update -y
apt-get install -y curl wget git python3 python3-pip python3-venv nginx software-properties-common

# 2. 安装 Node.js 20
echo "[2/6] 安装 Node.js 20..."
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" != "20" ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
node -v
npm -v

# 3. 创建工作目录
echo "[3/6] 创建工作目录..."
mkdir -p /opt/ai-data-platform

# 4. 配置 Nginx
echo "[4/6] 配置 Nginx..."
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

# 5. 配置 systemd 服务
echo "[5/6] 配置 systemd 服务..."
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
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

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
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# 6. 开放防火墙
echo "[6/6] 配置防火墙..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8787/tcp
ufw allow 8788/tcp
ufw --force enable

echo ""
echo "========================================"
echo "  基础环境部署完成！"
echo "========================================"
