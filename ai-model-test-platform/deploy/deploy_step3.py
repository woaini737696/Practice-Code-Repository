#!/usr/bin/env python3
"""步骤3: 构建并启动服务，配置Nginx"""
import json
import time
import base64
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

client = AcsClient('ALIBABA_CLOUD_ACCESS_KEY_ID', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'cn-shenzhen')
INSTANCE_ID = 'i-wz9egw4g1k2w0ml1hoy0'

def run_cmd(command, timeout=600):
    req = RunCommandRequest()
    req.set_accept_format('json')
    req.set_InstanceIds([INSTANCE_ID])
    req.set_CommandContent(command)
    req.set_Type('RunShellScript')
    req.set_Timeout(str(timeout))
    resp = client.do_action_with_exception(req)
    return json.loads(resp).get('InvokeId')

def get_result(invoke_id):
    for _ in range(120):
        time.sleep(10)
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
cd /opt/ai-model-test-platform
echo "=== 构建并启动Docker服务 ==="
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker ps -aq --filter "name=ai-test-" | xargs -r docker rm -f 2>/dev/null || true
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
echo "服务启动完成"
sleep 15
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "=== 配置Nginx反向代理 ==="
mkdir -p /etc/nginx/conf.d
cat > /etc/nginx/conf.d/ai-test.conf << 'NGINXEOF'
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
NGINXEOF
nginx -t && systemctl reload nginx
echo "Nginx配置完成"

echo ""
echo "=== 检查服务状态 ==="
curl -s http://localhost/health 2>/dev/null || echo "Health check failed"
docker ps --filter "name=ai-test-"
"""

print("[3/3] 构建并启动服务...")
print("这可能需要5-10分钟，请耐心等待...")
invoke_id = run_cmd(cmd, 600)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    print(f"退出码: {result.get('ExitCode')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
else:
    print("超时")

print("\n========================================")
print("部署完成！")
print("========================================")
print("访问地址: http://47.112.170.125")
print("默认账号: admin")
print("默认密码: admin123")
print("========================================")
