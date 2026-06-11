#!/usr/bin/env python3
"""检查服务器Node.js并部署前端"""
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

# 分块上传build.tar.gz到服务器
import os

with open('/tmp/build.tar.gz', 'rb') as f:
    data = f.read()

B64 = base64.b64encode(data).decode('utf-8')
CHUNK_SIZE = 50000
chunks = [B64[i:i+CHUNK_SIZE] for i in range(0, len(B64), CHUNK_SIZE)]
print(f"总大小: {len(data)} bytes, 分 {len(chunks)} 块")

# 先清理旧文件
cmd0 = "rm -f /tmp/build.tar.gz.b64 /tmp/build.tar.gz"
invoke_id = run_cmd(cmd0, 30)
get_result(invoke_id)

# 逐块上传
for i, chunk in enumerate(chunks):
    cmd = f"printf '%s' '{chunk}' >> /tmp/build.tar.gz.b64"
    invoke_id = run_cmd(cmd, 60)
    result = get_result(invoke_id)
    if result and result.get('InvocationStatus') == 'Success':
        print(f"块 {i+1}/{len(chunks)} 上传成功")
    else:
        print(f"块 {i+1}/{len(chunks)} 上传失败: {result}")
        break

# 解码并解压
cmd_final = """#!/bin/bash
set -e
echo "=== 解码并解压 ==="
base64 -d /tmp/build.tar.gz.b64 > /tmp/build.tar.gz 2>/dev/null
rm -f /tmp/build.tar.gz.b64
mkdir -p /opt/ai-model-test-platform/frontend/build
tar xzf /tmp/build.tar.gz -C /opt/ai-model-test-platform/frontend/build/
rm -f /tmp/build.tar.gz
echo "=== 验证 ==="
ls -la /opt/ai-model-test-platform/frontend/build/
echo "=== 完成 ==="
"""

print(f"\n解码并解压...")
invoke_id = run_cmd(cmd_final, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")