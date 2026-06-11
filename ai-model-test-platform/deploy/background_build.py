#!/usr/bin/env python3
"""后台构建前端，然后检查结果"""
import json, time, base64
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

def get_result(invoke_id, wait=60):
    for _ in range(wait):
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

# 第一步：后台启动构建
cmd1 = """#!/bin/bash
cd /opt/ai-model-test-platform/frontend
rm -rf build node_modules
nohup bash -c 'npm install --legacy-peer-deps && CI=false npm run build' > /tmp/build.log 2>&1 &
echo "Build PID: $!"
echo "Build started in background"
"""

print("[1/3] 后台启动构建...")
invoke_id = run_cmd(cmd1, 3600)
result = get_result(invoke_id, wait=10)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 等待30秒后检查构建状态
print("\n[2/3] 等待30秒后检查构建状态...")
time.sleep(30)

cmd2 = """#!/bin/bash
echo "=== Build log ==="
tail -20 /tmp/build.log 2>/dev/null || echo "No build log yet"
echo ""
echo "=== Build status ==="
ps aux | grep "npm\|node" | grep -v grep | head -5 || echo "No build process running"
echo ""
echo "=== Build output ==="
ls -la /opt/ai-model-test-platform/frontend/build/ 2>/dev/null || echo "Build directory not created yet"
"""

invoke_id = run_cmd(cmd2, 60)
result = get_result(invoke_id, wait=10)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")