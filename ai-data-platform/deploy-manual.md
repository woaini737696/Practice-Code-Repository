# AI数据分析平台 - 阿里云服务器手动部署指南

## 服务器信息
- **公网IP**: 47.112.170.125
- **实例ID**: i-wz9egw4g1k2w0ml1hoy0
- **地域**: 深圳 (cn-shenzhen)
- **操作系统**: Ubuntu 22.04
- **登录用户**: root
- **登录密码**: Ee9527ff

## 部署步骤

### 第一步：登录服务器
1. 打开阿里云控制台
2. 进入 ECS 实例列表
3. 找到实例 i-wz9egw4g1k2w0ml1hoy0
4. 点击"远程连接" -> "VNC连接"
5. 使用用户名 `root` 和密码 `Ee9527ff` 登录

### 第二步：执行环境初始化
在服务器上执行以下命令：

```bash
# 更新系统
apt-get update -y

# 安装基础依赖
apt-get install -y curl wget git python3 python3-pip python3-venv nginx

# 安装Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# 创建工作目录
mkdir -p /opt/ai-data-platform
```

### 第三步：上传项目代码
由于当前环境无法直接SSH到服务器，请使用以下方式上传代码：

**方式1：使用阿里云OSS**
1. 将项目代码打包为 zip 文件
2. 上传到阿里云OSS
3. 在服务器上下载

**方式2：使用scp（本地电脑有SSH权限时）**
```bash
# 在本地电脑执行
scp -r /path/to/ai-data-platform root@47.112.170.125:/opt/
```

**方式3：使用Git**
```bash
# 如果代码在Git仓库
cd /opt
git clone <你的仓库地址> ai-data-platform
```

### 第四步：安装依赖并构建
```bash
# 后端依赖
cd /opt/ai-data-platform/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖和构建
cd /opt/ai-data-platform/frontend
npm install
npm run build
```

### 第五步：配置Nginx
```bash
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
```

### 第六步：配置系统服务
```bash
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
systemctl enable ai-data-backend ai-data-frontend
```

### 第七步：启动服务
```bash
systemctl start ai-data-backend
systemctl start ai-data-frontend
```

### 第八步：验证部署
```bash
# 检查服务状态
systemctl status ai-data-backend
systemctl status ai-data-frontend

# 检查端口监听
ss -tlnp | grep -E "8787|8788"
```

## 访问地址
部署完成后，通过以下地址访问：
- **前端页面**: http://47.112.170.125
- **后端API**: http://47.112.170.125/api

## 配置数据库
编辑 `/opt/ai-data-platform/backend/.env` 文件，配置MySQL只读从库：
```bash
MYSQL_HOST=你的数据库地址
MYSQL_PORT=3306
MYSQL_USER=你的用户名
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=数据库名
```

配置完成后重启后端服务：
```bash
systemctl restart ai-data-backend
```

## 防火墙配置
安全组已配置以下端口开放：
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8787 (后端API)
- 8788 (前端开发)
