#!/usr/bin/env python3
"""全面诊断服务器状态"""
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
echo "1. 后端服务状态"
echo "========================================"
echo "--- 进程 ---"
ps aux | grep -E "uvicorn|python.*main" | grep -v grep || echo "❌ 无后端进程"

echo ""
echo "--- 端口8000 ---"
ss -tlnp | grep :8000 || echo "❌ 8000端口未监听"

echo ""
echo "--- 直接测试后端 ---"
curl -s http://localhost:8000/health 2>/dev/null || echo "❌ 后端无响应"

echo ""
echo "========================================"
echo "2. 前端文件状态"
echo "========================================"
echo "--- 前端目录 ---"
ls -la /opt/ai-model-test-platform/ 2>/dev/null || echo "❌ 项目目录不存在"
ls -la /opt/ai-model-test-platform/frontend/ 2>/dev/null || echo "❌ 前端目录不存在"

echo ""
echo "--- 前端index.html ---"
cat /opt/ai-model-test-platform/frontend/index.html 2>/dev/null | head -5 || echo "❌ index.html不存在"

echo ""
echo "========================================"
echo "3. Nginx容器状态"
echo "========================================"
docker ps --filter "name=app-nginx" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "❌ 无Nginx容器"

echo ""
echo "--- Nginx配置 ---"
docker exec app-nginx cat /etc/nginx/conf.d/default.conf 2>/dev/null | head -30 || echo "❌ 无法读取配置"

echo ""
echo "========================================"
echo "4. Docker容器状态"
echo "========================================"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "❌ Docker不可用"

echo ""
echo "========================================"
echo "5. Git仓库状态"
echo "========================================"
cd /opt/ai-model-test-platform 2>/dev/null || echo "❌ 项目目录不存在"
git status 2>/dev/null || echo "❌ 不是Git仓库"
git log --oneline -3 2>/dev/null || echo "❌ 无Git提交"
git remote -v 2>/dev/null || echo "❌ 无Git远程仓库"

echo ""
echo "========================================"
echo "6. 从外部测试"
echo "========================================"
echo "--- 根路径 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ 2>/dev/null || echo "❌ 无响应"

echo "--- /ai-test/ ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/ 2>/dev/null || echo "❌ 无响应"

echo "--- /ai-test/health ---"
curl -s http://localhost/ai-test/health 2>/dev/null || echo "❌ 无响应"

echo "--- /ai-test/api/ ---"
curl -s http://localhost/ai-test/api/ 2>/dev/null || echo "❌ 无响应"

echo "--- /guagua/ ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/ 2>/dev/null || echo "❌ 无响应"

echo "--- /ai-data/ ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/ 2>/dev/null || echo "❌ 无响应"

echo ""
echo "========================================"
echo "诊断完成"
echo "========================================"
"""

print("全面诊断服务器状态...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")