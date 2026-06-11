#!/usr/bin/env python3
"""
通过阿里云云助手API部署 - 使用Python在服务器上下载代码
"""

import json
import sys
import time
import os
import base64
import tarfile
import io

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

def upload_file_in_chunks(client, instance_id, local_path, remote_path):
    """将文件分块上传到服务器"""
    with open(local_path, 'r') as f:
        content = f.read()

    # 使用hex编码，分块上传
    hex_content = content.encode('utf-8').hex()
    chunk_size = 15000  # 每块约15KB hex = 7.5KB原始数据
    chunks = [hex_content[i:i+chunk_size] for i in range(0, len(hex_content), chunk_size)]

    # 初始化文件
    init_cmd = f"python3 -c \"open('{remote_path}', 'w').close()\""
    invoke_id = run_command(client, instance_id, init_cmd, timeout=30)
    get_command_result(client, invoke_id, instance_id)

    # 逐块追加
    for i, chunk in enumerate(chunks):
        append_cmd = f"python3 -c \"import binascii; f=open('{remote_path}', 'ab'); f.write(binascii.unhexlify('{chunk}')); f.close()\""
        invoke_id = run_command(client, instance_id, append_cmd, timeout=30)
        result = get_command_result(client, invoke_id, instance_id)
        if result['status'] != 'Success':
            print(f"  块 {i+1}/{len(chunks)} 失败: {result['status']}")
            return False
        print(f"  块 {i+1}/{len(chunks)} 完成")

    return True

def main():
    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)
    print(f"目标实例: {INSTANCE_ID}")

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
echo "Docker安装完成"
"""
    print("\n[1/5] 安装Docker...")
    invoke_id = run_command(client, INSTANCE_ID, step1, timeout=300)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    if result['status'] != 'Success':
        print(f"输出: {result['output']}")
        sys.exit(1)

    # 步骤2: 创建目录结构
    step2 = """#!/bin/bash
rm -rf /opt/ai-model-test-platform
mkdir -p /opt/ai-model-test-platform/backend/app/{api,core,models,schemas,services,tasks,websocket}
mkdir -p /opt/ai-model-test-platform/frontend/src/pages/{auth,tests,models,distillation,scoring,settings}
mkdir -p /opt/ai-model-test-platform/frontend/src/services
mkdir -p /opt/ai-model-test-platform/frontend/public
mkdir -p /opt/ai-model-test-platform/deploy
echo "目录创建完成"
"""
    print("\n[2/5] 创建目录结构...")
    invoke_id = run_command(client, INSTANCE_ID, step2, timeout=60)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")

    # 步骤3: 上传文件
    print("\n[3/5] 上传项目文件...")
    base = '/workspace/ai-model-test-platform'
    files = [
        ('backend/requirements.txt', '/opt/ai-model-test-platform/backend/requirements.txt'),
        ('backend/main.py', '/opt/ai-model-test-platform/backend/main.py'),
        ('backend/Dockerfile.prod', '/opt/ai-model-test-platform/backend/Dockerfile.prod'),
        ('backend/app/__init__.py', '/opt/ai-model-test-platform/backend/app/__init__.py'),
        ('backend/app/config.py', '/opt/ai-model-test-platform/backend/app/config.py'),
        ('backend/app/database.py', '/opt/ai-model-test-platform/backend/app/database.py'),
        ('backend/app/api/__init__.py', '/opt/ai-model-test-platform/backend/app/api/__init__.py'),
        ('backend/app/api/auth.py', '/opt/ai-model-test-platform/backend/app/api/auth.py'),
        ('backend/app/api/models.py', '/opt/ai-model-test-platform/backend/app/api/models.py'),
        ('backend/app/api/tests.py', '/opt/ai-model-test-platform/backend/app/api/tests.py'),
        ('backend/app/api/distillation.py', '/opt/ai-model-test-platform/backend/app/api/distillation.py'),
        ('backend/app/api/scoring.py', '/opt/ai-model-test-platform/backend/app/api/scoring.py'),
        ('backend/app/api/settings.py', '/opt/ai-model-test-platform/backend/app/api/settings.py'),
        ('backend/app/models/__init__.py', '/opt/ai-model-test-platform/backend/app/models/__init__.py'),
        ('backend/app/models/user.py', '/opt/ai-model-test-platform/backend/app/models/user.py'),
        ('backend/app/models/ai_model.py', '/opt/ai-model-test-platform/backend/app/models/ai_model.py'),
        ('backend/app/models/test.py', '/opt/ai-model-test-platform/backend/app/models/test.py'),
        ('backend/app/models/test_result.py', '/opt/ai-model-test-platform/backend/app/models/test_result.py'),
        ('backend/app/models/distilled_user.py', '/opt/ai-model-test-platform/backend/app/models/distilled_user.py'),
        ('backend/app/models/chat_record.py', '/opt/ai-model-test-platform/backend/app/models/chat_record.py'),
        ('backend/app/models/score_dimension.py', '/opt/ai-model-test-platform/backend/app/models/score_dimension.py'),
        ('backend/app/models/annotation.py', '/opt/ai-model-test-platform/backend/app/models/annotation.py'),
        ('backend/app/models/system_config.py', '/opt/ai-model-test-platform/backend/app/models/system_config.py'),
        ('backend/app/schemas/__init__.py', '/opt/ai-model-test-platform/backend/app/schemas/__init__.py'),
        ('backend/app/schemas/ai_model.py', '/opt/ai-model-test-platform/backend/app/schemas/ai_model.py'),
        ('backend/app/schemas/test.py', '/opt/ai-model-test-platform/backend/app/schemas/test.py'),
        ('backend/app/schemas/test_result.py', '/opt/ai-model-test-platform/backend/app/schemas/test_result.py'),
        ('backend/app/schemas/distilled_user.py', '/opt/ai-model-test-platform/backend/app/schemas/distilled_user.py'),
        ('backend/app/schemas/score_dimension.py', '/opt/ai-model-test-platform/backend/app/schemas/score_dimension.py'),
        ('backend/app/schemas/annotation.py', '/opt/ai-model-test-platform/backend/app/schemas/annotation.py'),
        ('backend/app/schemas/system_config.py', '/opt/ai-model-test-platform/backend/app/schemas/system_config.py'),
        ('backend/app/core/model_gateway.py', '/opt/ai-model-test-platform/backend/app/core/model_gateway.py'),
        ('backend/app/core/test_engine.py', '/opt/ai-model-test-platform/backend/app/core/test_engine.py'),
        ('backend/app/core/report_generator.py', '/opt/ai-model-test-platform/backend/app/core/report_generator.py'),
        ('backend/app/services/__init__.py', '/opt/ai-model-test-platform/backend/app/services/__init__.py'),
        ('backend/app/services/email_service.py', '/opt/ai-model-test-platform/backend/app/services/email_service.py'),
        ('backend/app/tasks/__init__.py', '/opt/ai-model-test-platform/backend/app/tasks/__init__.py'),
        ('backend/app/tasks/celery_app.py', '/opt/ai-model-test-platform/backend/app/tasks/celery_app.py'),
        ('backend/app/tasks/test_tasks.py', '/opt/ai-model-test-platform/backend/app/tasks/test_tasks.py'),
        ('backend/app/websocket/__init__.py', '/opt/ai-model-test-platform/backend/app/websocket/__init__.py'),
        ('backend/app/websocket/manager.py', '/opt/ai-model-test-platform/backend/app/websocket/manager.py'),
        ('frontend/package.json', '/opt/ai-model-test-platform/frontend/package.json'),
        ('frontend/tsconfig.json', '/opt/ai-model-test-platform/frontend/tsconfig.json'),
        ('frontend/Dockerfile.prod', '/opt/ai-model-test-platform/frontend/Dockerfile.prod'),
        ('frontend/nginx.conf', '/opt/ai-model-test-platform/frontend/nginx.conf'),
        ('frontend/public/index.html', '/opt/ai-model-test-platform/frontend/public/index.html'),
        ('frontend/public/manifest.json', '/opt/ai-model-test-platform/frontend/public/manifest.json'),
        ('frontend/src/index.tsx', '/opt/ai-model-test-platform/frontend/src/index.tsx'),
        ('frontend/src/App.tsx', '/opt/ai-model-test-platform/frontend/src/App.tsx'),
        ('frontend/src/App.css', '/opt/ai-model-test-platform/frontend/src/App.css'),
        ('frontend/src/index.css', '/opt/ai-model-test-platform/frontend/src/index.css'),
        ('frontend/src/services/api.ts', '/opt/ai-model-test-platform/frontend/src/services/api.ts'),
        ('frontend/src/services/websocket.ts', '/opt/ai-model-test-platform/frontend/src/services/websocket.ts'),
        ('frontend/src/pages/auth/LoginPage.tsx', '/opt/ai-model-test-platform/frontend/src/pages/auth/LoginPage.tsx'),
        ('frontend/src/pages/tests/TestList.tsx', '/opt/ai-model-test-platform/frontend/src/pages/tests/TestList.tsx'),
        ('frontend/src/pages/tests/TestDetail.tsx', '/opt/ai-model-test-platform/frontend/src/pages/tests/TestDetail.tsx'),
        ('frontend/src/pages/models/ModelList.tsx', '/opt/ai-model-test-platform/frontend/src/pages/models/ModelList.tsx'),
        ('frontend/src/pages/models/ModelDetail.tsx', '/opt/ai-model-test-platform/frontend/src/pages/models/ModelDetail.tsx'),
        ('frontend/src/pages/distillation/DistillationList.tsx', '/opt/ai-model-test-platform/frontend/src/pages/distillation/DistillationList.tsx'),
        ('frontend/src/pages/distillation/DistillationDetail.tsx', '/opt/ai-model-test-platform/frontend/src/pages/distillation/DistillationDetail.tsx'),
        ('frontend/src/pages/scoring/ScoringList.tsx', '/opt/ai-model-test-platform/frontend/src/pages/scoring/ScoringList.tsx'),
        ('frontend/src/pages/settings/SettingsPage.tsx', '/opt/ai-model-test-platform/frontend/src/pages/settings/SettingsPage.tsx'),
        ('docker-compose.prod.yml', '/opt/ai-model-test-platform/docker-compose.prod.yml'),
    ]

    success_count = 0
    for local_rel, remote_path in files:
        local_path = os.path.join(base, local_rel)
        if not os.path.exists(local_path):
            continue
        if upload_file_in_chunks(client, INSTANCE_ID, local_path, remote_path):
            success_count += 1
            print(f"  ✓ {local_rel}")
        else:
            print(f"  ✗ {local_rel}")

    print(f"\n上传完成: {success_count}/{len(files)} 个文件")

    # 步骤4: 构建并启动
    step4 = """#!/bin/bash
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
"""
    print("\n[4/5] 构建并启动服务...")
    invoke_id = run_command(client, INSTANCE_ID, step4, timeout=600)
    result = get_command_result(client, invoke_id, INSTANCE_ID)
    print(f"状态: {result['status']}")
    print(f"输出:\n{result['output']}")

    # 步骤5: 配置Nginx
    step5 = """#!/bin/bash
set -e
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
    print("\n[5/5] 配置Nginx...")
    invoke_id = run_command(client, INSTANCE_ID, step5, timeout=60)
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
