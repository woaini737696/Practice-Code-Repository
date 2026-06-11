#!/usr/bin/env python3
"""直接构建前端，设置长时间等待"""
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

def get_result(invoke_id, wait=120):
    for i in range(wait):
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
            status = r.get('InvocationStatus')
            if status in ['Success', 'Failed']:
                return r
            if i % 10 == 0:
                print(f"  等待中... ({i*5}s)")
    return None

# 第一步：npm install
cmd1 = """#!/bin/bash
set -e
cd /opt/ai-model-test-platform/frontend
rm -rf build node_modules
echo "=== npm install ==="
npm install --legacy-peer-deps 2>&1 | tail -5
echo "NPM_INSTALL_DONE"
"""

print("[1/3] npm install...")
invoke_id = run_cmd(cmd1, 600)
result = get_result(invoke_id, wait=120)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第二步：npm run build
cmd2 = """#!/bin/bash
set -e
cd /opt/ai-model-test-platform/frontend
echo "=== npm run build ==="
CI=false npm run build 2>&1 | tail -20
echo "BUILD_DONE"
ls -la /opt/ai-model-test-platform/frontend/build/
"""

print("\n[2/3] npm run build...")
invoke_id = run_cmd(cmd2, 600)
result = get_result(invoke_id, wait=120)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第三步：重启Nginx并验证
cmd3 = """#!/bin/bash
set -e
COMPOSE_DIR="/opt/ai-social/deploy"
echo "=== 修复权限 ==="
chmod -R 755 /opt/ai-model-test-platform/frontend/build/ 2>/dev/null || true
echo "=== 重启Nginx ==="
docker stop app-nginx 2>/dev/null || true
docker rm app-nginx 2>/dev/null || true
sleep 2
docker run -d \
  --name app-nginx \
  --restart unless-stopped \
  --network host \
  --user root \
  -v "$COMPOSE_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  -v "/opt/ai-model-test-platform/frontend/build:/opt/ai-model-test-platform/frontend/build:ro" \
  nginx:alpine
sleep 3
docker exec app-nginx nginx -t 2>&1 || true

echo ""
echo "=== 验证 ==="
echo "1. 根路径:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/
echo "2. AI-test:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/
echo "3. Health:"
curl -s http://localhost/ai-test/health
echo ""
echo "4. API Root:"
curl -s http://localhost/ai-test/api/
echo ""
echo "5. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/
echo "6. AI数据:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/
echo "DONE"
"""

print("\n[3/3] 重启Nginx并验证...")
invoke_id = run_cmd(cmd3, 120)
result = get_result(invoke_id, wait=30)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")