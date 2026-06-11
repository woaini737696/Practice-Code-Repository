#!/usr/bin/env python3
"""最终测试验证"""
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
set -e

echo "========================================"
echo "最终测试验证"
echo "========================================"

echo ""
echo "--- 1. 根路径 (项目列表) ---"
curl -s http://localhost/ | head -10

echo ""
echo "--- 2. AI数据分析中台 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "--- 3. AI模型测试平台前端 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/

echo ""
echo "--- 4. AI模型测试平台 Health ---"
curl -s http://localhost/ai-test/health

echo ""
echo "--- 5. AI模型测试平台 Models API ---"
curl -s http://localhost/ai-test/api/models

echo ""
echo "--- 6. AI模型测试平台 Auth 注册 (POST) ---"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "--- 7. AI模型测试平台 Auth 登录 (POST) ---"
curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=testuser&password=testpass123" http://localhost/ai-test/api/auth/login

echo ""
echo "--- 8. 检查Nginx错误日志 ---"
tail -5 /var/log/nginx/error.log 2>/dev/null | grep -v "notice" | grep -v "guagua" || echo "无相关错误"

echo ""
echo "========================================"
echo "测试完成！"
echo "========================================"
echo "访问地址:"
echo "  - 项目列表: http://47.112.170.125/"
echo "  - AI数据分析中台: http://47.112.170.125/ai-data/"
echo "  - AI模型测试平台: http://47.112.170.125/ai-test/"
echo ""
echo "AI模型测试平台API:"
echo "  - Health: http://47.112.170.125/ai-test/health"
echo "  - Models: http://47.112.170.125/ai-test/api/models"
echo "  - Auth: http://47.112.170.125/ai-test/api/auth/login"
echo ""
echo "默认账号: admin"
echo "默认密码: admin123"
echo "========================================"
"""

print("执行最终测试...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
