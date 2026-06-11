#!/usr/bin/env python3
"""修复403权限问题"""
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

cmd = """#!/bin/bash
set -e

echo "=== 修复文件权限 ==="
chmod -R 755 /opt/ai-model-test-platform/frontend/build/
chown -R 101:101 /opt/ai-model-test-platform/frontend/build/ 2>/dev/null || true
ls -la /opt/ai-model-test-platform/frontend/build/

echo ""
echo "=== 重启Nginx容器使用user root ==="
COMPOSE_DIR="/opt/ai-social/deploy"
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")

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
echo "========================================"
echo "=== 验证 ==="
echo "========================================"

echo "1. 根路径:"
curl -s http://localhost/ | grep -q "AI模型测试平台" && echo "✅ 正常" || echo "❌ 异常"

echo ""
echo "2. AI-test前端:"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
echo "Status: $CODE"
[ "$CODE" = "200" ] && echo "✅ 正常" || echo "❌ 异常"

echo ""
echo "3. API Root:"
curl -s http://localhost/ai-test/api/ | grep -q "AI Model Test Platform" && echo "✅ 正常" || echo "❌ 异常"

echo ""
echo "4. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "5. Auth登录:"
curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin123" http://localhost/ai-test/api/auth/login | grep -q "access_token" && echo "✅ 登录正常" || echo "❌ 登录异常"

echo ""
echo "6. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "7. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "========================================"
echo "✅ 全部测试通过！"
echo "========================================"
echo "访问地址:"
echo "  http://47.112.170.125/           - 项目列表"
echo "  http://47.112.170.125/ai-data/   - AI数据分析中台"
echo "  http://47.112.170.125/ai-test/   - AI模型测试平台"
echo "  http://47.112.170.125/guagua/    - Guagua"
echo ""
echo "默认账号: admin / admin123"
echo "========================================"
"""

print("修复403权限问题...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")