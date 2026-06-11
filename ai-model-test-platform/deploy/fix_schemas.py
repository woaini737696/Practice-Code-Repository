#!/usr/bin/env python3
"""修复schemas文件缺失问题"""
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

# 上传所有schemas文件
print("上传schemas文件...")
schema_files = [
    'backend/app/schemas/__init__.py',
    'backend/app/schemas/ai_model.py',
    'backend/app/schemas/annotation.py',
    'backend/app/schemas/distilled_user.py',
    'backend/app/schemas/score_dimension.py',
    'backend/app/schemas/system_config.py',
    'backend/app/schemas/test.py',
    'backend/app/schemas/test_result.py',
]

for rel_path in schema_files:
    local_path = os.path.join(BASE, rel_path)
    remote_path = f"/opt/ai-model-test-platform/{rel_path}"
    if not os.path.exists(local_path):
        continue
    if upload_file(local_path, remote_path):
        print(f"  ✓ {rel_path}")
    else:
        print(f"  ✗ {rel_path}")

# 重启后端服务
print("\n重启后端服务...")
cmd = """#!/bin/bash
set -e
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
