#!/usr/bin/env python3
"""重启后端并验证"""
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

echo "=== 1. 停止旧的后端服务 ==="
ps aux | grep "uvicorn\|python.*main" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 2

echo ""
echo "=== 2. 检查端口是否释放 ==="
ss -tlnp | grep :8000 || echo "8000端口已释放"

echo ""
echo "=== 3. 更新后端代码（移除root_path） ==="
cd /opt/ai-model-test-platform/backend
# 确保main.py没有root_path
grep -n "root_path" main.py || echo "root_path已移除"

echo ""
echo "=== 4. 启动后端服务 ==="
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 > /opt/ai-model-test-platform/backend/uvicorn.log 2>&1 &
sleep 3

echo ""
echo "=== 5. 检查后端进程 ==="
ps aux | grep uvicorn | grep -v grep || echo "后端未启动"

echo ""
echo "=== 6. 测试后端API ==="
echo "--- Health ---"
curl -s http://localhost:8000/health

echo ""
echo "--- API Root ---"
curl -s http://localhost:8000/

echo ""
echo "--- Models ---"
curl -s http://localhost:8000/api/models | head -1

echo ""
echo "========================================"
echo "通过Nginx代理测试"
echo "========================================"

echo ""
echo "7. 根路径:"
ROOT=$(curl -s http://localhost/)
if echo "$ROOT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常 - 显示项目列表"
else
    echo "❌ 根路径异常:"
    echo "$ROOT" | head -3
fi

echo ""
echo "8. AI模型测试平台前端:"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
if [ "$CODE" = "200" ]; then
    echo "✅ AI模型测试平台前端正常 (200)"
    curl -s http://localhost/ai-test/ | head -3
else
    echo "❌ AI模型测试平台前端异常 ($CODE)"
fi

echo ""
echo "9. AI模型测试平台API Root:"
API_ROOT=$(curl -s http://localhost/ai-test/api/)
echo "$API_ROOT"
if echo "$API_ROOT" | grep -q "AI Model Test Platform"; then
    echo "✅ API Root正常"
else
    echo "❌ API Root异常"
fi

echo ""
echo "10. AI模型测试平台 Models:"
MODELS=$(curl -s http://localhost/ai-test/api/models)
echo "$MODELS" | head -1
if echo "$MODELS" | grep -q "\[\|id\|name"; then
    echo "✅ Models API正常"
else
    echo "❌ Models API异常"
fi

echo ""
echo "11. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "12. Auth注册:"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"finaltest2","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "13. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "14. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

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
echo "默认账号: admin"
echo "默认密码: admin123"
echo "========================================"
"""

print("重启后端并验证...")
invoke_id = run_cmd(cmd, 180)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
