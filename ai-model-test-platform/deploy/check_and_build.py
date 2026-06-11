#!/usr/bin/env python3
"""
检查服务器上的代码并直接构建
"""

import json
import sys
import time

from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

ACCESS_KEY_ID = "ALIBABA_CLOUD_ACCESS_KEY_ID"
ACCESS_KEY_SECRET = "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
REGION_ID = "cn-shenzhen"
INSTANCE_ID = "i-wz9egw4g1k2w0ml1hoy0"

def run_command(client, instance_id, command, timeout=600):
    request = RunCommandRequest()
    request.set_accept_format('json')
    request.set_InstanceIds([instance_id])
    request.set_CommandContent(command)
    request.set_Type("RunShellScript")
    request.set_Timeout(str(timeout))
    request.set_WorkingDir("/root")
    response = client.do_action_with_exception(request)
    data = json.loads(response)
    return data.get('InvokeId')

def get_command_result(client, invoke_id, instance_id):
    request = DescribeInvocationResultsRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance_id)
    request.set_InvokeId(invoke_id)
    for _ in range(120):
        response = client.do_action_with_exception(request)
        data = json.loads(response)
        results = data.get('Invocation', {}).get('InvocationResults', {}).get('InvocationResult', [])
        if results:
            result = results[0]
            output = result.get('Output', '')
            exit_code = result.get('ExitCode', -1)
            status = result.get('InvocationStatus', '')
            if status in ['Success', 'Failed', 'Stopped']:
                return {'status': status, 'exit_code': exit_code, 'output': output}
        time.sleep(5)
    return {'status': 'Timeout', 'exit_code': -1, 'output': ''}

def main():
    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)

    # 检查服务器上的文件状态
    check_cmd = """#!/bin/bash
echo "=== 检查服务器状态 ==="
echo "Docker版本:"
docker --version 2>/dev/null || echo "Docker未安装"
docker-compose --version 2>/dev/null || echo "Docker Compose未安装"
echo ""
echo "项目目录内容:"
ls -la /opt/ai-model-test-platform/ 2>/dev/null || echo "项目目录不存在"
echo ""
echo "后端文件:"
ls -la /opt/ai-model-test-platform/backend/ 2>/dev/null || echo "backend目录不存在"
echo ""
echo "前端文件:"
ls -la /opt/ai-model-test-platform/frontend/ 2>/dev/null || echo "frontend目录不存在"
"""
    print("检查服务器状态...")
    invoke_id = run_command(client, INSTANCE_ID, check_cmd, timeout=60)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    print(f"输出:\n{result['output']}")

    # 如果文件已存在，直接构建
    build_cmd = """#!/bin/bash
set -e
cd /opt/ai-model-test-platform 2>/dev/null || { echo "项目目录不存在"; exit 1; }
echo "=== 构建并启动服务 ==="
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker ps -aq --filter "name=ai-test-" | xargs -r docker rm -f 2>/dev/null || true
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
echo "服务启动完成"
sleep 10
docker-compose -f docker-compose.prod.yml ps

echo "=== 配置Nginx ==="
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
"""
    print("\n构建并启动服务...")
    invoke_id = run_command(client, INSTANCE_ID, build_cmd, timeout=600)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    print(f"输出:\n{result['output']}")

if __name__ == '__main__':
    main()
