#!/usr/bin/env python3
"""快速测试"""
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

cmd = """#!/bin/bash
echo "=== 测试开始 ==="
echo "1. 根路径:"
curl -s http://localhost/ | head -1

echo "2. AI数据分析中台:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-data/
echo ""

echo "3. AI模型测试平台前端:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/
echo ""

echo "4. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "5. API Root:"
curl -s http://localhost/ai-test/api/

echo ""
echo "6. Models:"
curl -s http://localhost/ai-test/api/models | head -1

echo ""
echo "7. Auth注册:"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser10","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "8. Guagua:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/guagua/
echo ""

echo "9. 重定向检查:"
curl -s -L --max-redirs 5 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health
echo ""

echo "=== 测试结束 ==="
"""

print("执行快速测试...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
