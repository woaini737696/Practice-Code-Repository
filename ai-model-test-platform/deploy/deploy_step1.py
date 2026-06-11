#!/usr/bin/env python3
"""步骤1: 安装Docker环境"""
import json
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

client = AcsClient('ALIBABA_CLOUD_ACCESS_KEY_ID', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'cn-shenzhen')
INSTANCE_ID = 'i-wz9egw4g1k2w0ml1hoy0'

def run_cmd(command, timeout=300):
    req = RunCommandRequest()
    req.set_accept_format('json')
    req.set_InstanceIds([INSTANCE_ID])
    req.set_CommandContent(command)
    req.set_Type('RunShellScript')
    req.set_Timeout(str(timeout))
    resp = client.do_action_with_exception(req)
    return json.loads(resp).get('InvokeId')

def get_result(invoke_id):
    for _ in range(60):
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

cmd = """#!/bin/bash
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

print("[1/3] 安装Docker环境...")
invoke_id = run_cmd(cmd, 300)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    print(f"退出码: {result.get('ExitCode')}")
    import base64
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
else:
    print("超时")
