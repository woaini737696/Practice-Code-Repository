#!/usr/bin/env python3
"""构建后端镜像"""
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
echo "=== 构建后端镜像 ==="
docker build -f backend/Dockerfile.prod -t ai-test-backend:latest backend/
echo "后端镜像构建完成"
"""

print("构建后端镜像...")
invoke_id = run_cmd(cmd, 600)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    print(f"退出码: {result.get('ExitCode')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output[-3000:]}")
else:
    print("超时")
