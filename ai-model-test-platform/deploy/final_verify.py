#!/usr/bin/env python3
"""最终验证测试"""
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
echo "最终验证测试"
echo "========================================"

echo ""
echo "--- 1. 根路径 (项目列表) ---"
ROOT_RESULT=$(curl -s http://localhost/)
echo "$ROOT_RESULT" | head -5
if echo "$ROOT_RESULT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常"
else
    echo "❌ 根路径异常"
fi

echo ""
echo "--- 2. AI数据分析中台 ---"
AI_DATA_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-data/)
echo "Status: $AI_DATA_CODE"
if [ "$AI_DATA_CODE" = "200" ]; then
    echo "✅ AI数据分析中台正常"
else
    echo "❌ AI数据分析中台异常"
fi

echo ""
echo "--- 3. AI模型测试平台前端 ---"
AI_TEST_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
echo "Status: $AI_TEST_CODE"
if [ "$AI_TEST_CODE" = "200" ]; then
    echo "✅ AI模型测试平台前端正常"
else
    echo "❌ AI模型测试平台前端异常"
fi

echo ""
echo "--- 4. AI模型测试平台 Health ---"
HEALTH_RESULT=$(curl -s http://localhost/ai-test/health)
echo "$HEALTH_RESULT"
if echo "$HEALTH_RESULT" | grep -q "healthy"; then
    echo "✅ Health正常"
else
    echo "❌ Health异常"
fi

echo ""
echo "--- 5. AI模型测试平台 API Root ---"
API_ROOT=$(curl -s http://localhost/ai-test/api/)
echo "$API_ROOT"
if echo "$API_ROOT" | grep -q "AI Model Test Platform"; then
    echo "✅ API Root正常"
else
    echo "❌ API Root异常"
fi

echo ""
echo "--- 6. AI模型测试平台 Models API ---"
MODELS_RESULT=$(curl -s http://localhost/ai-test/api/models)
echo "$MODELS_RESULT" | head -3
if echo "$MODELS_RESULT" | grep -q "\["; then
    echo "✅ Models API正常"
else
    echo "❌ Models API异常"
fi

echo ""
echo "--- 7. AI模型测试平台 Auth 注册 (POST) ---"
AUTH_RESULT=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser9","password":"testpass123"}' http://localhost/ai-test/api/auth/register)
echo "$AUTH_RESULT"
if echo "$AUTH_RESULT" | grep -q "id\|success\|message"; then
    echo "✅ Auth注册正常"
else
    echo "❌ Auth注册异常"
fi

echo ""
echo "--- 8. Guagua项目 ---"
GUAGUA_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/guagua/)
echo "Status: $GUAGUA_CODE"
if [ "$GUAGUA_CODE" = "200" ]; then
    echo "✅ Guagua正常"
else
    echo "❌ Guagua异常"
fi

echo ""
echo "--- 9. 检查重定向循环 ---"
# 检查是否有301/302循环
REDIRECT_COUNT=$(curl -s -L --max-redirs 5 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health)
echo "重定向次数: $REDIRECT_COUNT"
if [ "$REDIRECT_COUNT" -lt 3 ]; then
    echo "✅ 无重定向循环"
else
    echo "❌ 可能存在重定向循环"
fi

echo ""
echo "--- 10. Docker Nginx错误日志 ---"
docker exec app-nginx sh -c 'tail -3 /var/log/nginx/error.log 2>/dev/null || echo "无错误日志"'

echo ""
echo "========================================"
echo "测试完成！"
echo "========================================"
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

print("执行最终验证测试...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
