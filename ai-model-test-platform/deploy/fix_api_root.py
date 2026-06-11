#!/usr/bin/env python3
"""修复API Root路径问题"""
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

cmd = """#!/bin/bash
set -e

COMPOSE_DIR="/opt/ai-social/deploy"

# 获取Guagua容器真实IP
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")

echo "Guagua前端IP: $GUAGUA_FRONTEND_IP"
echo "Guagua后端IP: $GUAGUA_BACKEND_IP"

echo ""
echo "=== 修复Nginx配置：正确处理API路径 ==="
mkdir -p $COMPOSE_DIR/nginx

cat > $COMPOSE_DIR/nginx/default.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # 根路径 - 项目列表
    location = / {
        return 200 '<!DOCTYPE html><html><head><meta charset="utf-8"><title>服务器项目列表</title><style>body{font-family:Arial,sans-serif;max-width:800px;margin:50px auto;padding:20px;background:#f5f5f5;}h1{color:#333;border-bottom:2px solid #1890ff;padding-bottom:10px;}ul{list-style:none;padding:0;}li{margin:15px 0;}a{display:block;padding:15px 20px;background:white;border-radius:8px;text-decoration:none;color:#1890ff;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}a:hover{transform:translateX(5px);box-shadow:0 4px 12px rgba(0,0,0,0.15);}</style></head><body><h1>服务器项目列表</h1><ul><li><a href="/ai-data/">AI数据分析中台</a></li><li><a href="/ai-test/">AI模型测试平台</a></li><li><a href="/guagua/">Guagua</a></li></ul></body></html>';
        add_header Content-Type text/html;
        add_header Cache-Control no-cache;
    }

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://127.0.0.1:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://127.0.0.1:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # AI模型测试平台 - /ai-test/
    # 前端静态文件
    location /ai-test/ {
        alias /opt/ai-model-test-platform/frontend/;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # API根路径 - 直接代理到后端根路径
    location = /ai-test/api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # API子路径 - 保留/api/前缀代理到后端
    location /ai-test/api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    location /ai-test/ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ai-test/health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # Guagua项目 - 使用Docker容器IP
    location /guagua/ {
        proxy_pass http://GUAGUA_FRONTEND_IP:80/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /guagua/api/ {
        proxy_pass http://GUAGUA_BACKEND_IP:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 替换Guagua IP
sed -i "s/GUAGUA_FRONTEND_IP/$GUAGUA_FRONTEND_IP/g" $COMPOSE_DIR/nginx/default.conf
sed -i "s/GUAGUA_BACKEND_IP/$GUAGUA_BACKEND_IP/g" $COMPOSE_DIR/nginx/default.conf

echo ""
echo "=== 重载Nginx配置 ==="
docker exec app-nginx nginx -t && docker exec app-nginx nginx -s reload

echo ""
echo "========================================"
echo "测试验证"
echo "========================================"

echo ""
echo "1. 根路径:"
ROOT=$(curl -s http://localhost/)
if echo "$ROOT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常"
else
    echo "❌ 根路径异常"
fi

echo ""
echo "2. AI模型测试平台前端:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/

echo ""
echo "3. API Root (通过Nginx):"
API_ROOT=$(curl -s http://localhost/ai-test/api/)
echo "$API_ROOT"
if echo "$API_ROOT" | grep -q "AI Model Test Platform"; then
    echo "✅ API Root正常"
else
    echo "❌ API Root异常"
fi

echo ""
echo "4. Models API:"
MODELS=$(curl -s http://localhost/ai-test/api/models)
echo "$MODELS"
if echo "$MODELS" | grep -q "\[\]"; then
    echo "✅ Models API正常"
else
    echo "❌ Models API异常"
fi

echo ""
echo "5. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "6. Auth注册:"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"finaltest4","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "7. Auth登录:"
LOGIN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=finaltest4&password=testpass123" http://localhost/ai-test/api/auth/login)
if echo "$LOGIN" | grep -q "access_token"; then
    echo "✅ 登录正常"
else
    echo "❌ 登录异常: $LOGIN"
fi

echo ""
echo "8. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "9. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "10. 重定向循环检查:"
REDIRECTS=$(curl -s -L --max-redirs 10 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health)
if [ "$REDIRECTS" = "0" ]; then
    echo "✅ 无重定向循环"
else
    echo "❌ 重定向次数: $REDIRECTS"
fi

echo ""
echo "========================================"
echo "测试完成！"
echo "========================================"
echo "访问地址:"
echo "  - 项目列表: http://47.112.170.125/"
echo "  - AI数据分析中台: http://47.112.170.125/ai-data/"
echo "  - AI模型测试平台: http://47.112.170.125/ai-test/"
echo "  - Guagua: http://47.112.170.125/guagua/"
echo ""
echo "默认账号: admin"
echo "默认密码: admin123"
echo "========================================"
"""

print("修复API Root路径问题...")
invoke_id = run_cmd(cmd, 180)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
