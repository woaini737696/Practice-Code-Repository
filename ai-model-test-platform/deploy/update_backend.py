#!/usr/bin/env python3
"""更新后端代码并重启服务"""
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

# 上传修复后的main.py
with open('/workspace/ai-model-test-platform/backend/main.py', 'r') as f:
    content = f.read()
b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
cmd = f"echo '{b64}' | base64 -d > /opt/ai-model-test-platform/backend/main.py"
invoke_id = run_cmd(cmd, 60)
result = get_result(invoke_id)
print(f"main.py上传: {result.get('InvocationStatus') if result else 'timeout'}")

# 重启后端服务并测试
cmd2 = """#!/bin/bash
set -e

# 停止旧进程
pkill -f "uvicorn main:app" || true
sleep 2

# 启动后端服务
cd /opt/ai-model-test-platform/backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > /var/log/ai-test-backend.log 2>&1 &
sleep 5

echo "=== 测试API ==="
echo "--- Health ---"
curl -s http://localhost:8000/health || echo "Health failed"

echo ""
echo "--- Root ---"
curl -s http://localhost:8000/ || echo "Root failed"

echo ""
echo "--- API Docs ---"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs || echo "Docs failed"

echo ""
echo "--- Nginx代理测试 ---"
curl -s http://localhost/ai-test/health || echo "Nginx health failed"

echo ""
echo "--- Nginx前端测试 ---"
curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/ || echo "Nginx frontend failed"

echo ""
echo "--- Nginx API测试 ---"
curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/api/ || echo "Nginx API failed"

echo ""
echo "=== 完成 ==="
"""

print("\n重启后端并测试...")
invoke_id = run_cmd(cmd2, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
