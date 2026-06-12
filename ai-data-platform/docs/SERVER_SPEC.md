# 服务器部署规范 (SERVER_SPEC.md)

## 服务器资源
- **实例**: i-wz9egw4g1k2w0ml1hoy0 (阿里云 华南1 深圳)
- **IP**: 47.112.170.125
- **规格**: 2核CPU / 2GB内存
- **OS**: Ubuntu 24.04

---

## 核心原则

### 1. 禁止在服务器上构建
- **禁止** `npm install`、`npm run build`、`mvn build`、`pip install` 等构建/安装命令
- 所有构建在本地完成，只上传构建产物到服务器
- 前端：本地 `npm run build` 后上传 `out/` 目录
- 后端：本地打包后上传，服务器只运行已安装好的 venv

### 2. Swap 配置
- 已配置 3GB Swap (1GB + 2GB)
- 防止 OOM Killer 杀死进程
- 检查命令: `swapon --show`

### 3. Docker 内存限制
- **Java 容器**: 512MB 上限
- **前端容器**: 64MB 上限  
- **Nginx 容器**: 32MB 上限
- 启动时必须指定 `--memory` 参数

### 4. 宝塔面板
- 已停用，不使用宝塔管理服务
- 使用 systemd 管理宿主机服务
- 使用 Docker Compose 管理容器服务

### 5. 多项目路径隔离
- 所有项目通过 Docker Nginx (app-nginx) 统一入口
- 每个项目独立路径前缀，互不冲突
- 详见: `docs/multi-project-deployment-guide.md`

---

## 当前项目清单

| 项目 | 路径前缀 | 部署方式 | 前端端口 | 后端端口 | 内存限制 |
|------|---------|---------|---------|---------|---------|
| AI数据分析中台 | `/ai-data/` | systemd + 静态文件 | Nginx静态 | 8787 | 后端512MB |
| Guagua | `/guagua/` | Docker Compose | 80(Docker) | 8080(Docker) | 前端64MB/后端512MB |
| AI模型测试 | `/ai-test/` | Nginx静态 | 静态文件 | 8000 | - |

---

## 端口分配规范

| 端口范围 | 用途 |
|---------|------|
| 80 | Docker Nginx 统一入口 |
| 443 | HTTPS (Docker Nginx) |
| 8000-8099 | AI测试平台 |
| 8787-8788 | AI数据分析中台 |
| 9000-9999 | 预留新项目 |

---

## systemd 服务规范

### AI数据分析中台

```ini
# /etc/systemd/system/ai-data-backend.service
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
MemoryMax=512M
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 前端不再使用 systemd 管理
- 改用 Nginx 直接托管静态文件
- 节省内存，避免 Node.js 进程占用

---

## 部署流程

### 前端部署
```bash
# 1. 本地构建
cd frontend
npm ci
npm run build
# 产物在 out/ 目录

# 2. 上传到服务器
tar -czf frontend.tar.gz -C out .
scp frontend.tar.gz root@47.112.170.125:/tmp/

# 3. 服务器部署
ssh root@47.112.170.125
mkdir -p /opt/ai-data-platform/frontend/out
tar -xzf /tmp/frontend.tar.gz -C /opt/ai-data-platform/frontend/out/
rm -rf /opt/ai-data-platform/frontend/node_modules  # 清理构建依赖
```

### 后端部署
```bash
# 后端代码更新后重启服务
systemctl restart ai-data-backend
```

---

## Nginx 配置（Docker app-nginx）

### 前端静态文件
```nginx
location /ai-data/ {
    alias /opt/ai-data-platform/frontend/out/;
    index index.html;
    try_files $uri $uri/ /ai-data/index.html;
}

location /ai-data/api/ {
    proxy_pass http://172.25.138.178:8787/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

---

## 内存监控

```bash
# 查看内存使用
free -h

# 查看各进程内存
ps aux --sort=-%mem | head -10

# 查看 Docker 容器内存
docker stats --no-stream

# 查看 OOM 历史
dmesg | grep -i oom
```

---

## 故障恢复

### 502 Bad Gateway
1. 检查后端服务: `systemctl status ai-data-backend`
2. 检查端口: `ss -tlnp | grep 8787`
3. 重启后端: `systemctl restart ai-data-backend`
4. 检查 Nginx 配置: `docker exec app-nginx nginx -t`

### 服务未启动
1. 检查 Swap 是否充足: `free -h`
2. 检查是否 OOM: `dmesg | grep -i oom`
3. 适当增加 Swap 或减少内存占用

### 前端静态文件更新
```bash
# 本地构建后上传
tar -czf frontend.tar.gz -C out .
scp frontend.tar.gz root@47.112.170.125:/tmp/
ssh root@47.112.170.125 "rm -rf /opt/ai-data-platform/frontend/out/* && tar -xzf /tmp/frontend.tar.gz -C /opt/ai-data-platform/frontend/out/"
```