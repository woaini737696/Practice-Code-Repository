#!/usr/bin/env python3
"""最终全面检查"""
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
echo "最终全面检查"
echo "========================================"

ALL_PASS=true

echo ""
echo "--- 1. 根路径 (项目列表) ---"
ROOT=$(curl -s http://localhost/)
if echo "$ROOT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常 - 包含所有项目链接"
else
    echo "❌ 根路径异常"
    ALL_PASS=false
fi

echo ""
echo "--- 2. AI数据分析中台 ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-data/)
if [ "$CODE" = "200" ]; then
    echo "✅ AI数据分析中台正常 (200)"
else
    echo "❌ AI数据分析中台异常 ($CODE)"
    ALL_PASS=false
fi

echo ""
echo "--- 3. AI模型测试平台前端 ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
if [ "$CODE" = "200" ]; then
    echo "✅ AI模型测试平台前端正常 (200)"
else
    echo "❌ AI模型测试平台前端异常 ($CODE)"
    ALL_PASS=false
fi

echo ""
echo "--- 4. AI模型测试平台 Health ---"
HEALTH=$(curl -s http://localhost/ai-test/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Health正常: $HEALTH"
else
    echo "❌ Health异常: $HEALTH"
    ALL_PASS=false
fi

echo ""
echo "--- 5. AI模型测试平台 Models API ---"
MODELS=$(curl -s http://localhost/ai-test/api/models)
if echo "$MODELS" | grep -q "\[\|id\|name"; then
    echo "✅ Models API正常"
else
    echo "❌ Models API异常: $MODELS"
    ALL_PASS=false
fi

echo ""
echo "--- 6. AI模型测试平台 Auth 注册 ---"
AUTH=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"finaltest","password":"testpass123"}' http://localhost/ai-test/api/auth/register)
if echo "$AUTH" | grep -q "注册成功\|user_id"; then
    echo "✅ Auth注册正常: $AUTH"
else
    echo "❌ Auth注册异常: $AUTH"
    ALL_PASS=false
fi

echo ""
echo "--- 7. AI模型测试平台 Auth 登录 ---"
LOGIN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=finaltest&password=testpass123" http://localhost/ai-test/api/auth/login)
if echo "$LOGIN" | grep -q "access_token"; then
    echo "✅ Auth登录正常"
else
    echo "❌ Auth登录异常: $LOGIN"
    ALL_PASS=false
fi

echo ""
echo "--- 8. Guagua项目 ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/guagua/)
if [ "$CODE" = "200" ]; then
    echo "✅ Guagua正常 (200)"
else
    echo "❌ Guagua异常 ($CODE)"
    ALL_PASS=false
fi

echo ""
echo "--- 9. 检查重定向循环 ---"
REDIRECTS=$(curl -s -L --max-redirs 10 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health)
if [ "$REDIRECTS" = "0" ]; then
    echo "✅ 无重定向循环"
else
    echo "❌ 重定向次数: $REDIRECTS"
    ALL_PASS=false
fi

echo ""
echo "--- 10. Nginx错误日志检查 ---"
ERRORS=$(docker exec app-nginx sh -c 'tail -5 /var/log/nginx/error.log 2>/dev/null | grep -v "notice" | wc -l')
if [ "$ERRORS" = "0" ]; then
    echo "✅ Nginx无错误"
else
    echo "⚠️ Nginx有 $ERRORS 条非notice日志"
fi

echo ""
echo "========================================"
if [ "$ALL_PASS" = true ]; then
    echo "✅ 所有测试通过！系统正常运行！"
else
    echo "❌ 部分测试未通过，请检查 above"
fi
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 项目列表: http://47.112.170.125/"
echo "  - AI数据分析中台: http://47.112.170.125/ai-data/"
echo "  - AI模型测试平台: http://47.112.170.125/ai-test/"
echo "  - Guagua: http://47.112.170.125/guagua/"
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

print("执行最终全面检查...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
