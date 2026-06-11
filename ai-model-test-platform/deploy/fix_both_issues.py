#!/usr/bin/env python3
"""一次性修复两个问题的脚本"""
import json
import time
import base64
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

client = AcsClient('ALIBABA_CLOUD_ACCESS_KEY_ID', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'cn-shenzhen')
INSTANCE_ID = 'i-wz9egw4g1k2w0ml1hoy0'

def run_cmd(command, timeout=60):
    req = RunCommandRequest()
    req.set_accept_format('json')
    req.set_InstanceIds([INSTANCE_ID])
    req.set_CommandContent(command)
    req.set_Type('RunShellScript')
    req.set_Timeout(str(timeout))
    resp = client.do_action_with_exception(req)
    return json.loads(resp).get('InvokeId')

def get_result(invoke_id):
    for _ in range(30):
        time.sleep(5)
        req = DescribeInvocationResultsRequest()
        req.set_accept_format('json')
        req.set_InstanceId(INSTANCE_ID)
        req.set_InvokeId(invoke_id)
        resp = client.do_action_with_exception(req)
        d = json.loads(resp)
        results = d.get('Invocation', {}).get('InvocationResults', {}).get('InvocationResult', [])
        if results:
            r = results[0]
            if r.get('InvocationStatus') in ['Success', 'Failed', 'Aborted']:
                return r
    return None

# 诊断问题
cmd1 = """#!/bin/bash
set -e

echo "=== 1. 检查Nginx容器状态 ==="
docker ps --filter "name=app-nginx" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== 2. 检查Nginx当前配置 ==="
docker exec app-nginx cat /etc/nginx/conf.d/default.conf 2>/dev/null | head -30 || echo "无法读取配置"

echo ""
echo "=== 3. 检查前端文件是否存在 ==="
ls -la /opt/ai-model-test-platform/frontend/ 2>/dev/null | head -10 || echo "前端目录不存在"

echo ""
echo "=== 4. 检查前端index.html ==="
ls -la /opt/ai-model-test-platform/frontend/index.html 2>/dev/null || echo "index.html不存在"

echo ""
echo "=== 5. 测试直接访问前端文件 ==="
curl -s -o /dev/null -w "直接访问前端文件: %{http_code}\n" http://localhost/ai-test/index.html 2>/dev/null || echo "无法访问"

echo ""
echo "=== 6. 测试访问AI-test根路径 ==="
curl -s -o /dev/null -w "访问/ai-test/: %{http_code}\n" http://localhost/ai-test/ 2>/dev/null || echo "无法访问"

echo ""
echo "=== 7. 测试访问根路径 ==="
curl -s -o /dev/null -w "访问根路径: %{http_code}\n" http://localhost/ 2>/dev/null || echo "无法访问"

echo ""
echo "=== 8. 检查宿主机Nginx配置 ==="
cat /etc/nginx/sites-enabled/* 2>/dev/null | head -20 || echo "无sites-enabled配置"
"""

print("[1/3] 诊断问题...")
invoke_id = run_cmd(cmd1, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 修复问题
cmd2 = """#!/bin/bash
set -e

COMPOSE_DIR="/opt/ai-social/deploy"

# 获取Guagua容器真实IP
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")

echo "Guagua前端IP: $GUAGUA_FRONTEND_IP"
echo "Guagua后端IP: $GUAGUA_BACKEND_IP"

echo ""
echo "=== 修复1: 创建完整的Nginx配置（包含根路径项目列表和AI-test前端） ==="
mkdir -p $COMPOSE_DIR/nginx

# 创建项目列表HTML文件
mkdir -p $COMPOSE_DIR/nginx/html
cat > $COMPOSE_DIR/nginx/html/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>服务器项目列表</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; border-bottom: 2px solid #1890ff; padding-bottom: 10px; }
        ul { list-style: none; padding: 0; }
        li { margin: 15px 0; }
        a {
            display: block;
            padding: 15px 20px;
            background: white;
            border-radius: 8px;
            text-decoration: none;
            color: #1890ff;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        a:hover { transform: translateX(5px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-left: 10px;
        }
        .badge-primary { background: #e6f7ff; color: #1890ff; }
    </style>
</head>
<body>
    <h1>服务器项目列表</h1>
    <ul>
        <li><a href="/ai-data/">AI数据分析中台 <span class="badge badge-primary">数据分析</span></a></li>
        <li><a href="/ai-test/">AI模型测试平台 <span class="badge badge-primary">模型测试</span></a></li>
        <li><a href="/guagua/">Guagua <span class="badge badge-primary">社交应用</span></a></li>
    </ul>
</body>
</html>
HTMLEOF

cat > $COMPOSE_DIR/nginx/default.conf << EOF
server {
    listen 80;
    server_name _;

    # 根路径 - 项目列表
    location = / {
        root /usr/share/nginx/html;
        index index.html;
    }

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://127.0.0.1:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://127.0.0.1:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # AI模型测试平台 - /ai-test/
    # 前端静态文件
    location /ai-test/ {
        alias /opt/ai-model-test-platform/frontend/;
        index index.html;
        try_files \$uri \$uri/ /ai-test/index.html;
    }

    # API请求
    location /ai-test/api/ {
        rewrite ^/ai-test/api/(.*)\$ /api/\$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    location /ai-test/ws {
        rewrite ^/ai-test/ws\$ /ws break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /ai-test/health {
        rewrite ^/ai-test/health\$ /health break;
        proxy_pass http://127.0.0.1:8000;
    }

    # Guagua项目 - 使用Docker容器IP
    location /guagua/ {
        proxy_pass http://$GUAGUA_FRONTEND_IP:80/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /guagua/api/ {
        proxy_pass http://$GUAGUA_BACKEND_IP:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo ""
echo "=== 修复2: 确保前端文件存在 ==="
if [ ! -d "/opt/ai-model-test-platform/frontend" ]; then
    echo "前端目录不存在，需要重新构建..."
    # 尝试从源码构建
    if [ -d "/opt/ai-model-test-platform" ]; then
        cd /opt/ai-model-test-platform/frontend
        npm install 2>/dev/null || echo "npm install失败"
        npm run build 2>/dev/null || echo "npm run build失败"
    fi
else
    echo "前端目录存在"
    ls -la /opt/ai-model-test-platform/frontend/index.html 2>/dev/null || echo "index.html不存在"
fi

echo ""
echo "=== 修复3: 重启Nginx容器并挂载所有必要文件 ==="
docker stop app-nginx 2>/dev/null || true
docker rm app-nginx 2>/dev/null || true
sleep 2

docker run -d \
  --name app-nginx \
  --restart unless-stopped \
  --network host \
  -v "$COMPOSE_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  -v "$COMPOSE_DIR/nginx/html:/usr/share/nginx/html:ro" \
  -v "/opt/ai-model-test-platform/frontend:/opt/ai-model-test-platform/frontend:ro" \
  nginx:alpine

sleep 3

echo ""
echo "=== 测试Nginx配置 ==="
docker exec app-nginx nginx -t 2>&1 || true

echo ""
echo "=== 检查容器状态 ==="
docker ps --filter "name=app-nginx" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
"""

print("\n[2/3] 修复问题...")
invoke_id = run_cmd(cmd2, 180)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 验证修复
cmd3 = """#!/bin/bash
set -e

echo "========================================"
echo "验证修复结果"
echo "========================================"

echo ""
echo "--- 1. 根路径 (项目列表) ---"
ROOT=$(curl -s http://localhost/)
if echo "$ROOT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常 - 显示项目列表"
    echo "$ROOT" | head -5
else
    echo "❌ 根路径异常:"
    echo "$ROOT" | head -5
fi

echo ""
echo "--- 2. AI模型测试平台前端 ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
if [ "$CODE" = "200" ]; then
    echo "✅ AI模型测试平台前端正常 (200)"
    curl -s http://localhost/ai-test/ | head -3
else
    echo "❌ AI模型测试平台前端异常 ($CODE)"
fi

echo ""
echo "--- 3. AI模型测试平台API ---"
curl -s http://localhost/ai-test/api/ | head -1

echo ""
echo "--- 4. Health ---"
curl -s http://localhost/ai-test/health

echo ""
echo "--- 5. Guagua ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "--- 6. AI数据分析中台 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "========================================"
echo "验证完成！"
echo "========================================"
"""

print("\n[3/3] 验证修复...")
invoke_id = run_cmd(cmd3, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
