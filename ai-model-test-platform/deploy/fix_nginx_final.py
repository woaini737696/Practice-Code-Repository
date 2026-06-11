#!/usr/bin/env python3
"""修复Nginx配置，正确处理API路径"""
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

# 更新Nginx配置 - 使用rewrite正确处理路径
cmd = """#!/bin/bash
set -e

cat > /etc/nginx/sites-available/ai-data-platform << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://localhost:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://localhost:8787/api/;
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

    # API代理 - 去掉/ai-test前缀，直接转发到后端
    location /ai-test/api/ {
        rewrite ^/ai-test/api/(.*)$ /api/$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    # WebSocket代理
    location /ai-test/ws {
        rewrite ^/ai-test/ws$ /ws break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health检查
    location /ai-test/health {
        rewrite ^/ai-test/health$ /health break;
        proxy_pass http://127.0.0.1:8000;
    }

    # 默认首页
    location = / {
        return 200 '
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>服务器项目列表</title></head>
        <body style="font-family:Arial,sans-serif;max-width:800px;margin:50px auto;padding:20px;">
        <h1>服务器项目列表</h1>
        <ul>
        <li><a href="/ai-data/">AI数据分析中台</a></li>
        <li><a href="/ai-test/">AI模型测试平台</a></li>
        </ul>
        </body>
        </html>';
        add_header Content-Type text/html;
    }
}
NGINXEOF

nginx -t && systemctl reload nginx
echo "Nginx配置更新完成"
"""

print("[1/2] 更新Nginx配置...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 测试所有端点
cmd2 = """#!/bin/bash
set -e

echo "=== 全面测试 ==="

echo "--- 1. 根路径 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/

echo ""
echo "--- 2. AI数据分析中台 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "--- 3. AI模型测试平台前端 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/

echo ""
echo "--- 4. AI模型测试平台Health ---"
curl -s http://localhost/ai-test/health

echo ""
echo "--- 5. AI模型测试平台API Root ---"
curl -s http://localhost/ai-test/api/

echo ""
echo "--- 6. AI模型测试平台Auth API ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/api/auth/login

echo ""
echo "--- 7. AI模型测试平台Models API ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/api/models

echo ""
echo "--- 8. AI模型测试平台Docs ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/api/docs

echo ""
echo "=== Nginx错误日志 ==="
tail -3 /var/log/nginx/error.log 2>/dev/null || echo "无错误"

echo ""
echo "=== 测试完成 ==="
"""

print("\n[2/2] 全面测试...")
invoke_id = run_cmd(cmd2, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
