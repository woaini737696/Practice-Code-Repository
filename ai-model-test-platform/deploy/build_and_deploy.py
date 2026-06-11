#!/usr/bin/env python3
"""在服务器上构建前端并更新配置"""
import json, time, base64
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

# 修复后端main.py（移除root_path）
cmd1 = """#!/bin/bash
set -e

echo "=== 1. 修复后端main.py（移除root_path） ==="
sed -i '/root_path=/d' /opt/ai-model-test-platform/backend/main.py 2>/dev/null
# 如果没有root_path行，直接替换整个文件
if grep -q "root_path" /opt/ai-model-test-platform/backend/main.py 2>/dev/null; then
    python3 -c "
import re
with open('/opt/ai-model-test-platform/backend/main.py', 'r') as f:
    content = f.read()
content = re.sub(r'root_path=.+?\\)', '', content)
with open('/opt/ai-model-test-platform/backend/main.py', 'w') as f:
    f.write(content)
"
fi
echo "✅ 后端main.py已修复"
grep -n "root_path" /opt/ai-model-test-platform/backend/main.py || echo "已确认无root_path"

echo ""
echo "=== 2. 重启后端服务 ==="
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 2
cd /opt/ai-model-test-platform/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 > /opt/ai-model-test-platform/backend/uvicorn.log 2>&1 &
sleep 3
ps aux | grep uvicorn | grep -v grep || echo "❌ 后端未启动"

echo ""
echo "=== 3. 测试后端 ==="
curl -s http://localhost:8000/health
curl -s http://localhost:8000/
"""

print("[1/3] 修复后端...")
invoke_id = run_cmd(cmd1, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 构建前端
cmd2 = """#!/bin/bash
set -e

echo "=== 4. 构建前端 ==="
cd /opt/ai-model-test-platform/frontend
npm install 2>&1 | tail -3
CI=false npm run build 2>&1 | tail -10

echo ""
echo "=== 5. 验证构建产物 ==="
ls -lh /opt/ai-model-test-platform/frontend/build/
echo "✅ 构建完成"
"""

print("\n[2/3] 构建前端...")
invoke_id = run_cmd(cmd2, 300)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 更新Nginx配置并验证
cmd3 = """#!/bin/bash
set -e

COMPOSE_DIR="/opt/ai-social/deploy"
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")

echo "=== 6. 更新Nginx配置（指向build目录） ==="
mkdir -p $COMPOSE_DIR/nginx

printf '%s\\n' 'server {' \
    '    listen 80;' \
    '    server_name _;' \
    '' \
    '    location = / {' \
    '        return 200 '"'"'<!DOCTYPE html><html><head><meta charset="utf-8"><title>服务器项目列表</title><style>body{font-family:Arial,sans-serif;max-width:800px;margin:50px auto;padding:20px;background:#f5f5f5;}h1{color:#333;border-bottom:2px solid #1890ff;padding-bottom:10px;}ul{list-style:none;padding:0;}li{margin:15px 0;}a{display:block;padding:15px 20px;background:white;border-radius:8px;text-decoration:none;color:#1890ff;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}a:hover{transform:translateX(5px);box-shadow:0 4px 12px rgba(0,0,0,0.15);}</style></head><body><h1>服务器项目列表</h1><ul><li><a href="/ai-data/">AI数据分析中台</a></li><li><a href="/ai-test/">AI模型测试平台</a></li><li><a href="/guagua/">Guagua</a></li></ul></body></html>'"'"';' \
    '        add_header Content-Type text/html;' \
    '        add_header Cache-Control no-cache;' \
    '    }' \
    '' \
    '    location /ai-data/ {' \
    '        proxy_pass http://127.0.0.1:8788/ai-data/;' \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Upgrade $http_upgrade;' \
    '        proxy_set_header Connection "upgrade";' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_cache_bypass $http_upgrade;' \
    '    }' \
    '' \
    '    location /ai-data/api/ {' \
    '        proxy_pass http://127.0.0.1:8787/api/;' \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '    }' \
    '' \
    '    location /ai-test/ {' \
    '        alias /opt/ai-model-test-platform/frontend/build/;' \
    '        index index.html;' \
    '        try_files $uri $uri/ /ai-test/index.html;' \
    '    }' \
    '' \
    '    location = /ai-test/api/ {' \
    '        proxy_pass http://127.0.0.1:8000/;' \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '    }' \
    '' \
    '    location /ai-test/api/ {' \
    '        proxy_pass http://127.0.0.1:8000/api/;' \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Prefix /ai-test;' \
    '    }' \
    '' \
    '    location /ai-test/ws {' \
    '        proxy_pass http://127.0.0.1:8000/ws;' \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Upgrade $http_upgrade;' \
    '        proxy_set_header Connection "upgrade";' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '    }' \
    '' \
    '    location /ai-test/health {' \
    '        proxy_pass http://127.0.0.1:8000/health;' \
    '    }' \
    '' \
    '    location /guagua/ {' \
    "        proxy_pass http://$GUAGUA_FRONTEND_IP:80/;" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '' \
    '    location /guagua/api/ {' \
    "        proxy_pass http://$GUAGUA_BACKEND_IP:8080/api/;" \
    '        proxy_http_version 1.1;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '    }' \
    '}' > $COMPOSE_DIR/nginx/default.conf

echo ""
echo "=== 7. 重启Nginx容器 ==="
docker stop app-nginx 2>/dev/null || true
docker rm app-nginx 2>/dev/null || true
sleep 2
docker run -d \
  --name app-nginx \
  --restart unless-stopped \
  --network host \
  -v "$COMPOSE_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  -v "/opt/ai-model-test-platform/frontend/build:/opt/ai-model-test-platform/frontend/build:ro" \
  nginx:alpine
sleep 3
docker exec app-nginx nginx -t 2>&1 || true

echo ""
echo "========================================"
echo "=== 8. 全面验证 ==="
echo "========================================"

echo "1. 根路径:"
ROOT=$(curl -s http://localhost/)
echo "$ROOT" | grep -q "AI模型测试平台" && echo "✅ 正常" || echo "❌ 异常"

echo ""
echo "2. AI-test前端:"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
echo "Status: $CODE"
curl -s http://localhost/ai-test/ | head -5

echo ""
echo "3. API Root:"
API=$(curl -s http://localhost/ai-test/api/)
echo "$API"
echo "$API" | grep -q "AI Model Test Platform" && echo "✅ 正常" || echo "❌ 异常"

echo ""
echo "4. Models:"
curl -s http://localhost/ai-test/api/models

echo ""
echo "5. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "6. Auth注册:"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"finaltest99","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "7. Auth登录:"
curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=finaltest99&password=testpass123" http://localhost/ai-test/api/auth/login | grep -q "access_token" && echo "✅ 登录正常" || echo "❌ 登录异常"

echo ""
echo "8. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "9. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "10. 重定向检查:"
R=$(curl -s -L --max-redirs 10 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health)
echo "重定向: $R"

echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo "访问地址:"
echo "  http://47.112.170.125/           - 项目列表"
echo "  http://47.112.170.125/ai-data/   - AI数据分析中台"
echo "  http://47.112.170.125/ai-test/   - AI模型测试平台"
echo "  http://47.112.170.125/guagua/    - Guagua"
echo ""
echo "默认账号: admin / admin123"
echo "========================================"
"""

print("\n[3/3] 更新Nginx并验证...")
invoke_id = run_cmd(cmd3, 180)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")