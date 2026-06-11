# 多项目共存部署规范指南

## 服务器信息
- **IP**: 47.112.170.125
- **区域**: 阿里云 华南1（深圳）
- **实例ID**: i-wz9egw4g1k2w0ml1hoy0

---

## 架构设计

### 核心原则
1. **单一入口**: 所有项目通过 Docker Nginx (app-nginx) 的80端口统一接入
2. **路径隔离**: 每个项目拥有独立的路径前缀，互不冲突
3. **网络分层**:
   - Docker项目（Guagua）→ Docker内部网络通信
   - 宿主机项目（AI数据平台、AI测试平台）→ 通过宿主机IP访问
4. **端口规范**: 每个宿主机项目分配独立端口段

### 当前项目分配

| 项目 | 路径前缀 | 前端端口 | 后端端口 | 部署方式 | 状态 |
|------|---------|---------|---------|---------|------|
| AI数据分析中台 | `/ai-data/` | 8788 | 8787 | systemd + 宿主机 | 运行中 |
| AI模型测试平台 | `/ai-test/` | - | 8000 | systemd + 宿主机 | 运行中 |
| Guagua | `/guagua/` | 80(Docker) | 8080(Docker) | Docker Compose | 运行中 |

### 访问地址

- **项目列表首页**: http://47.112.170.125/
- **AI数据分析中台**: http://47.112.170.125/ai-data/
- **AI模型测试平台**: http://47.112.170.125/ai-test/
- **Guagua**: http://47.112.170.125/guagua/

---

## Nginx 统一网关配置

### 配置文件位置
宿主机: `/opt/app-nginx-default.conf`
容器内: `/etc/nginx/conf.d/default.conf`

### 关键配置说明

```nginx
server {
    listen 80;
    server_name _;

    # AI数据分析中台 - 宿主机服务
    location /ai-data/ {
        proxy_pass http://172.25.138.178:8788/ai-data/;
        # ... 标准代理头
    }

    location /ai-data/api/ {
        proxy_pass http://172.25.138.178:8787/api/;
    }

    # Guagua - Docker内部服务
    location /guagua/ {
        proxy_pass http://guagua-frontend:80/;
        # ... 标准代理头
    }

    location /guagua/api/ {
        proxy_pass http://guagua-backend:8080/api/;
    }

    # 根路径项目导航页
    location = / {
        return 200 '<html>...项目列表...</html>';
    }
}
```

### 重要注意事项
1. **宿主机IP**: 必须使用实际网卡IP（如 `172.25.138.178`），不能用 `127.0.0.1` 或 `localhost`
2. **Docker网络**: app-nginx 必须加入目标项目的Docker网络（如 `deploy_app-net`）
3. **Linux限制**: `host.docker.internal` 在Linux Docker默认不可用，必须用宿主机IP

---

## 防火墙配置

### UFW规则
```bash
# 允许Docker网络访问宿主机应用端口
ufw allow from 172.17.0.0/16 to any port 8787 proto tcp
ufw allow from 172.17.0.0/16 to any port 8788 proto tcp
ufw allow from 172.17.0.0/16 to any port 8000 proto tcp

ufw allow from 172.18.0.0/16 to any port 8787 proto tcp
ufw allow from 172.18.0.0/16 to any port 8788 proto tcp
ufw allow from 172.18.0.0/16 to any port 8000 proto tcp
```

### 安全组规则（阿里云控制台）
确保安全组已开放:
- 80/tcp (HTTP)
- 443/tcp (HTTPS)

内部端口（8787, 8788, 8000）不需要对外暴露，只需Docker内部访问。

---

## 新增项目规范流程

### 步骤1: 申请资源
- 路径前缀（如 `/new-project/`）
- 端口号（宿主机项目需要）
- 部署方式（Docker / systemd）

### 步骤2: 宿主机项目部署
```bash
# 1. 分配端口（避免冲突）
# 建议端口段：
# - AI数据平台: 8787-8788
# - AI测试平台: 8000-8001
# - 新项目: 建议 9000+ 或按顺序分配

# 2. 服务监听 0.0.0.0（不是 127.0.0.1）
# 例如: uvicorn app.main:app --host 0.0.0.0 --port 9000

# 3. 添加防火墙规则
ufw allow from 172.17.0.0/16 to any port 9000 proto tcp
ufw allow from 172.18.0.0/16 to any port 9000 proto tcp
```

### 步骤3: 更新Nginx配置
```bash
# 编辑 /opt/app-nginx-default.conf
# 添加新的 location 块

# 宿主机项目示例:
location /new-project/ {
    proxy_pass http://172.25.138.178:9000/new-project/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# Docker项目示例:
location /new-project/ {
    proxy_pass http://new-project-frontend:80/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# 重载Nginx
docker exec app-nginx nginx -s reload
```

### 步骤4: 更新项目列表页
修改根路径 `location = /` 的HTML，添加新项目链接。

---

## 故障排查

### 问题1: Docker Nginx无法访问宿主机服务
**症状**: 502 Bad Gateway 或 timeout
**排查**:
```bash
# 1. 确认宿主机服务监听地址
ss -tlnp | grep <端口>
# 应该显示 0.0.0.0:<端口>，不是 127.0.0.1:<端口>

# 2. 确认防火墙
ufw status | grep <端口>

# 3. 从Docker容器测试
docker exec app-nginx wget -qO- --timeout=5 http://<宿主机IP>:<端口>/
```

### 问题2: 路径前缀冲突
**症状**: 访问A项目却显示B项目内容
**解决**: 确保每个项目的 `location` 路径唯一，且 `proxy_pass` 末尾的 `/` 使用正确。

### 问题3: 静态资源404
**症状**: 页面结构正常但CSS/JS加载失败
**解决**: 确保前端项目配置了正确的 `basePath`（Next.js）或 `publicPath`（Webpack）。

---

## 维护命令

```bash
# 查看所有项目状态
docker ps
systemctl status ai-data-backend ai-data-frontend

# 查看Nginx访问日志
docker exec app-nginx tail -f /var/log/nginx/access.log

# 查看Nginx错误日志
docker exec app-nginx tail -f /var/log/nginx/error.log

# 重启所有AI数据平台服务
systemctl restart ai-data-backend ai-data-frontend

# 重启Nginx网关
docker restart app-nginx

# 查看端口占用
ss -tlnp
```

---

## 联系信息
- 服务器管理员: root
- 阿里云控制台: https://ecs.console.aliyun.com
