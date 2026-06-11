#!/usr/bin/env python3
"""
最小化部署：通过云助手直接在服务器上创建文件并部署
每批只上传1个文件，避免命令长度超限
"""

import json
import sys
import time
import os

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

def upload_file(client, instance_id, local_path, remote_path):
    """上传单个文件，使用base64编码"""
    with open(local_path, 'r') as f:
        content = f.read()

    # base64编码
    b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')

    # 如果base64太长，分块上传
    chunk_size = 12000  # 每块约12KB base64
    if len(b64) <= chunk_size:
        # 小文件直接上传
        cmd = f"""echo '{b64}' | base64 -d > {remote_path}"""
        invoke_id = run_command(client, instance_id, cmd, timeout=60)
        result = get_command_result(client, invoke_id, instance_id)
        return result['status'] == 'Success'
    else:
        # 大文件分块上传
        chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

        # 初始化空文件
        cmd = f"> {remote_path}"
        invoke_id = run_command(client, instance_id, cmd, timeout=30)
        get_command_result(client, invoke_id, instance_id)

        for i, chunk in enumerate(chunks):
            cmd = f"""echo '{chunk}' | base64 -d >> {remote_path}"""
            invoke_id = run_command(client, instance_id, cmd, timeout=60)
            result = get_command_result(client, invoke_id, instance_id)
            if result['status'] != 'Success':
                print(f"    块 {i+1}/{len(chunks)} 失败")
                return False

        return True

import base64

def main():
    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)
    print(f"目标实例: {INSTANCE_ID}")

    base = '/workspace/ai-model-test-platform'

    # 步骤1: 安装Docker
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

# 创建目录结构
mkdir -p backend/app/{api,core,models,schemas,services,tasks,websocket}
mkdir -p frontend/src/{pages/{auth,tests,models,distillation,scoring,settings},services}
mkdir -p frontend/public

echo "环境准备完成"
"""
    print("\n[1/3] 安装Docker...")
    invoke_id = run_command(client, INSTANCE_ID, step1, timeout=300)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    if result['status'] != 'Success':
        print(f"输出: {result['output']}")
        sys.exit(1)

    # 步骤2: 上传所有文件（逐个上传）
    print("\n[2/3] 上传项目文件...")

    all_files = [
        'backend/requirements.txt',
        'backend/main.py',
        'backend/Dockerfile.prod',
        'backend/app/__init__.py',
        'backend/app/config.py',
        'backend/app/database.py',
        'backend/app/api/__init__.py',
        'backend/app/api/auth.py',
        'backend/app/api/models.py',
        'backend/app/api/tests.py',
        'backend/app/api/distillation.py',
        'backend/app/api/scoring.py',
        'backend/app/api/settings.py',
        'backend/app/models/__init__.py',
        'backend/app/models/user.py',
        'backend/app/models/ai_model.py',
        'backend/app/models/test.py',
        'backend/app/models/test_result.py',
        'backend/app/models/distilled_user.py',
        'backend/app/models/chat_record.py',
        'backend/app/models/score_dimension.py',
        'backend/app/models/annotation.py',
        'backend/app/models/system_config.py',
        'backend/app/schemas/__init__.py',
        'backend/app/core/model_gateway.py',
        'backend/app/core/test_engine.py',
        'backend/app/core/report_generator.py',
        'backend/app/services/__init__.py',
        'backend/app/services/email_service.py',
        'backend/app/tasks/__init__.py',
        'backend/app/tasks/celery_app.py',
        'backend/app/tasks/test_tasks.py',
        'backend/app/websocket/__init__.py',
        'backend/app/websocket/manager.py',
        'frontend/package.json',
        'frontend/tsconfig.json',
        'frontend/Dockerfile.prod',
        'frontend/nginx.conf',
        'frontend/public/index.html',
        'frontend/public/manifest.json',
        'frontend/src/index.tsx',
        'frontend/src/App.tsx',
        'frontend/src/App.css',
        'frontend/src/index.css',
        'frontend/src/services/api.ts',
        'frontend/src/services/websocket.ts',
        'frontend/src/pages/auth/LoginPage.tsx',
        'frontend/src/pages/tests/TestList.tsx',
        'frontend/src/pages/tests/TestDetail.tsx',
        'frontend/src/pages/models/ModelList.tsx',
        'frontend/src/pages/models/ModelDetail.tsx',
        'frontend/src/pages/distillation/DistillationList.tsx',
        'frontend/src/pages/distillation/DistillationDetail.tsx',
        'frontend/src/pages/scoring/ScoringList.tsx',
        'frontend/src/pages/settings/SettingsPage.tsx',
        'docker-compose.prod.yml',
    ]

    success_count = 0
    for i, rel_path in enumerate(all_files):
        local_path = os.path.join(base, rel_path)
        remote_path = f"/opt/ai-model-test-platform/{rel_path}"
        if not os.path.exists(local_path):
            continue

        if upload_file(client, INSTANCE_ID, local_path, remote_path):
            success_count += 1
            print(f"  [{i+1}/{len(all_files)}] ✓ {rel_path}")
        else:
            print(f"  [{i+1}/{len(all_files)}] ✗ {rel_path}")

    print(f"\n上传完成: {success_count}/{len(all_files)} 个文件")

    # 步骤3: 构建并启动
    step3 = """#!/bin/bash
set -e
cd /opt/ai-model-test-platform
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
    print("\n[3/3] 构建并启动服务...")
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
