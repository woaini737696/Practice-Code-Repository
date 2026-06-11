#!/usr/bin/env python3
"""修复数据库路径问题"""
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

# 上传修复后的config.py
with open('/workspace/ai-model-test-platform/backend/app/config.py', 'r') as f:
    content = f.read()
b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
cmd = f"echo '{b64}' | base64 -d > /opt/ai-model-test-platform/backend/app/config.py"
invoke_id = run_cmd(cmd, 60)
result = get_result(invoke_id)
print(f"config.py上传: {result.get('InvocationStatus') if result else 'timeout'}")

# 创建数据库目录并启动服务
cmd = """#!/bin/bash
set -e
mkdir -p /opt/ai-model-test-platform/backend
chmod 777 /opt/ai-model-test-platform/backend

# 停止旧进程
pkill -f "uvicorn main:app" || true
sleep 2

# 启动后端服务
cd /opt/ai-model-test-platform/backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > /var/log/ai-test-backend.log 2>&1 &
sleep 5
curl -s http://localhost:8000/health || echo "Health check failed"
curl -s http://localhost:8000/ || echo "Root check failed"
"""

invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
