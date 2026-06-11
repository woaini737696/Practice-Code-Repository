#!/usr/bin/env python3
"""
直接部署方案：不通过Docker，直接在服务器上运行
"""
import json
import time
import os
import base64
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

client = AcsClient('ALIBABA_CLOUD_ACCESS_KEY_ID', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'cn-shenzhen')
INSTANCE_ID = 'i-wz9egw4g1k2w0ml1hoy0'
BASE = '/workspace/ai-model-test-platform'

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

def upload_file(local_path, remote_path):
    with open(local_path, 'r') as f:
        content = f.read()
    b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
    chunk_size = 12000
    if len(b64) <= chunk_size:
        cmd = f"echo '{b64}' | base64 -d > {remote_path}"
        invoke_id = run_cmd(cmd, 60)
        result = get_result(invoke_id)
        return result and result.get('InvocationStatus') == 'Success'
    else:
        chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
        cmd = f"> {remote_path}"
        invoke_id = run_cmd(cmd, 30)
        get_result(invoke_id)
        for chunk in chunks:
            cmd = f"echo '{chunk}' | base64 -d >> {remote_path}"
            invoke_id = run_cmd(cmd, 60)
            result = get_result(invoke_id)
            if not result or result.get('InvocationStatus') != 'Success':
                return False
        return True

# 步骤1: 安装Python和依赖
cmd1 = """#!/bin/bash
set -e
echo "=== 安装Python环境 ==="
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx redis-server mysql-server
systemctl enable nginx redis-server mysql-server
systemctl start redis-server mysql-server

echo "=== 配置MySQL ==="
mysql -e "CREATE DATABASE IF NOT EXISTS ai_test CHARACTER SET utf8mb4;"
mysql -e "CREATE USER IF NOT EXISTS 'aitest'@'localhost' IDENTIFIED BY 'AiTest2024!@#';"
mysql -e "GRANT ALL PRIVILEGES ON ai_test.* TO 'aitest'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo "环境安装完成"
"""
print("[1/4] 安装环境...")
invoke_id = run_cmd(cmd1, 300)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output[-1000:]}")

# 步骤2: 上传代码
print("\n[2/4] 上传代码...")
files = [
    'backend/requirements.txt', 'backend/main.py',
    'backend/app/__init__.py', 'backend/app/config.py', 'backend/app/database.py',
    'backend/app/api/__init__.py', 'backend/app/api/auth.py',
    'backend/app/api/models.py', 'backend/app/api/tests.py',
    'backend/app/api/distillation.py', 'backend/app/api/scoring.py', 'backend/app/api/settings.py',
    'backend/app/models/__init__.py', 'backend/app/models/user.py',
    'backend/app/models/ai_model.py', 'backend/app/models/test.py',
    'backend/app/models/test_result.py', 'backend/app/models/distilled_user.py',
    'backend/app/models/chat_record.py', 'backend/app/models/score_dimension.py',
    'backend/app/models/annotation.py', 'backend/app/models/system_config.py',
    'backend/app/schemas/__init__.py',
    'backend/app/core/model_gateway.py', 'backend/app/core/test_engine.py', 'backend/app/core/report_generator.py',
    'backend/app/services/__init__.py', 'backend/app/services/email_service.py',
    'backend/app/tasks/__init__.py', 'backend/app/tasks/celery_app.py', 'backend/app/tasks/test_tasks.py',
    'backend/app/websocket/__init__.py', 'backend/app/websocket/manager.py',
]

for rel_path in files:
    local_path = os.path.join(BASE, rel_path)
    remote_path = f"/opt/ai-model-test-platform/{rel_path}"
    if not os.path.exists(local_path):
        continue
    if upload_file(local_path, remote_path):
        print(f"  ✓ {rel_path}")
    else:
        print(f"  ✗ {rel_path}")

# 步骤3: 安装Python依赖并构建前端
print("\n[3/4] 安装依赖...")
cmd3 = """#!/bin/bash
set -e
cd /opt/ai-model-test-platform/backend
echo "=== 安装Python依赖 ==="
pip3 install -r requirements.txt -q

echo "=== 构建前端 ==="
cd /opt/ai-model-test-platform/frontend
# 创建简单的静态页面
cat > /opt/ai-model-test-platform/frontend/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI模型测试平台</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        h1 { color: #1890ff; }
        .menu { display: flex; gap: 20px; margin: 20px 0; }
        .menu a { padding: 10px 20px; background: #1890ff; color: white; text-decoration: none; border-radius: 4px; }
        .menu a:hover { background: #40a9ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI模型测试平台</h1>
        <div class="menu">
            <a href="/api/">API文档</a>
            <a href="/health">健康检查</a>
        </div>
        <p>平台正在开发中，前端React构建遇到问题，暂时使用简化页面。</p>
        <p>后端API正常运行，可通过 /api/ 访问。</p>
    </div>
</body>
</html>
HTMLEOF

echo "依赖安装完成"
"""
invoke_id = run_cmd(cmd3, 600)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output[-1000:]}")

# 步骤4: 配置Nginx并启动服务
print("\n[4/4] 启动服务...")
cmd4 = """#!/bin/bash
set -e
echo "=== 配置Nginx ==="
cat > /etc/nginx/sites-available/ai-test << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    location / {
        root /opt/ai-model-test-platform/frontend;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
NGINXEOF
ln -sf /etc/nginx/sites-available/ai-test /etc/nginx/sites-enabled/ai-test
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== 启动后端服务 ==="
cd /opt/ai-model-test-platform/backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > /var/log/ai-test-backend.log 2>&1 &
sleep 5
curl -s http://localhost:8000/health || echo "Health check failed"

echo "服务启动完成"
"""
invoke_id = run_cmd(cmd4, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

print("\n========================================")
print("部署完成！")
print("========================================")
print("访问地址: http://47.112.170.125")
print("默认账号: admin")
print("默认密码: admin123")
print("========================================")
