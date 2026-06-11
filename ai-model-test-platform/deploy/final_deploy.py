#!/usr/bin/env python3
"""
最终部署方案：通过云助手发送命令，在服务器上启动Python HTTP服务器接收文件
"""

import json
import sys
import time
import os
import http.server
import socketserver
import threading

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
    print(f"目标实例: {INSTANCE_ID}")

    # 步骤1: 安装Docker并创建目录
    step1 = """#!/bin/bash
set -e
echo "=== 安装Docker ==="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
docker --version
docker-compose --version

rm -rf /opt/ai-model-test-platform
mkdir -p /opt/ai-model-test-platform
cd /opt/ai-model-test-platform

# 启动临时HTTP服务器接收文件
python3 -m http.server 18888 &
echo "HTTP服务器启动在端口18888"
echo "Docker安装完成"
"""
    print("\n[1/3] 安装Docker并启动文件接收服务...")
    invoke_id = run_command(client, INSTANCE_ID, step1, timeout=300)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    if result['status'] != 'Success':
        print(f"输出: {result['output']}")
        sys.exit(1)

    # 步骤2: 打包代码并通过HTTP上传到服务器
    print("\n[2/3] 打包并上传代码...")
    import tarfile
    import io
    import urllib.request

    base = '/workspace/ai-model-test-platform'
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as tar:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'build']]
            for file in files:
                if file.endswith(('.pyc', '.log', '.db')):
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, base)
                tar.add(filepath, arcname=arcname)

    tarball = output.getvalue()
    print(f"打包完成，大小: {len(tarball)} bytes")

    # 通过HTTP POST上传到服务器
    print("上传到服务器...")
    try:
        req = urllib.request.Request(
            'http://47.112.170.125:18888/ai-test-code.tar.gz',
            data=tarball,
            method='PUT',
            headers={'Content-Type': 'application/gzip'}
        )
        response = urllib.request.urlopen(req, timeout=30)
        print(f"上传成功: {response.status}")
    except Exception as e:
        print(f"上传失败: {e}")
        print("尝试通过curl上传...")
        # 备用方案：使用curl
        with open('/tmp/ai-test-code.tar.gz', 'wb') as f:
            f.write(tarball)
        os.system("curl -X PUT --data-binary @/tmp/ai-test-code.tar.gz http://47.112.170.125:18888/ai-test-code.tar.gz")

    # 步骤3: 解压并部署
    step3 = """#!/bin/bash
set -e
cd /opt/ai-model-test-platform
echo "=== 解压代码 ==="
if [ -f ai-test-code.tar.gz ]; then
    tar -xzf ai-test-code.tar.gz
    rm ai-test-code.tar.gz
    echo "代码解压完成"
else
    echo "错误: 未找到代码包"
    exit 1
fi

# 停止临时HTTP服务器
pkill -f "python3 -m http.server 18888" || true

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
    print("\n[3/3] 解压并部署...")
    invoke_id = run_command(client, INSTANCE_ID, step3, timeout=600)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    print(f"输出:\n{result['output']}")

    print("\n========================================")
    print("部署完成！")
    print("========================================")
    print("访问地址: http://47.112.170.125")
    print("默认账号: admin")
    print("默认密码: admin123")
    print("========================================")

if __name__ == '__main__':
    main()
