#!/usr/bin/env python3
"""强制重启Nginx容器使新配置生效"""
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

COMPOSE_DIR="/opt/ai-social/deploy"

# 获取Guagua容器真实IP
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")

echo "Guagua前端IP: $GUAGUA_FRONTEND_IP"
echo "Guagua后端IP: $GUAGUA_BACKEND_IP"

echo ""
echo "=== 1. 检查宿主机上的配置文件 ==="
cat $COMPOSE_DIR/nginx/default.conf | grep -E "proxy_pass|listen|location" | head -20

echo ""
echo "=== 2. 检查容器内的配置文件 ==="
docker exec app-nginx cat /etc/nginx/conf.d/default.conf | grep -E "proxy_pass|listen|location" | head -20

echo ""
echo "=== 3. 删除旧容器并重新创建 ==="
docker stop app-nginx 2>/dev/null || true
docker rm app-nginx 2>/dev/null || true
sleep 2

docker run -d \
  --name app-nginx \
  --restart unless-stopped \
  --network host \
  -v "$COMPOSE_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  -v "/opt/ai-model-test-platform/frontend:/opt/ai-model-test-platform/frontend:ro" \
  nginx:alpine

sleep 3

echo ""
echo "=== 4. 验证容器内配置 ==="
docker exec app-nginx cat /etc/nginx/conf.d/default.conf | grep -E "proxy_pass|listen|location" | head -20

echo ""
echo "=== 5. 测试Nginx配置 ==="
docker exec app-nginx nginx -t 2>&1 || true

echo ""
echo "========================================"
echo "全面测试验证"
echo "========================================"

echo ""
echo "1. 根路径:"
ROOT=$(curl -s http://localhost/)
if echo "$ROOT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常"
else
    echo "❌ 根路径异常"
    echo "$ROOT" | head -3
fi

echo ""
echo "2. AI模型测试平台前端:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/

echo ""
echo "3. API Root (通过Nginx):"
API_ROOT=$(curl -s http://localhost/ai-test/api/)
echo "$API_ROOT"
if echo "$API_ROOT" | grep -q "AI Model Test Platform"; then
    echo "✅ API Root正常"
else
    echo "❌ API Root异常"
fi

echo ""
echo "4. Models API:"
MODELS=$(curl -s http://localhost/ai-test/api/models)
echo "$MODELS"
if echo "$MODELS" | grep -q "\[\]"; then
    echo "✅ Models API正常"
else
    echo "❌ Models API异常"
fi

echo ""
echo "5. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "6. Auth注册:"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"finaltest6","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "7. Auth登录:"
LOGIN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=finaltest6&password=testpass123" http://localhost/ai-test/api/auth/login)
if echo "$LOGIN" | grep -q "access_token"; then
    echo "✅ 登录正常"
else
    echo "❌ 登录异常: $LOGIN"
fi

echo ""
echo "8. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "9. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "10. 重定向循环检查:"
REDIRECTS=$(curl -s -L --max-redirs 10 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health)
if [ "$REDIRECTS" = "0" ]; then
    echo "✅ 无重定向循环"
else
    echo "❌ 重定向次数: $REDIRECTS"
fi

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

print("强制重启Nginx容器...")
invoke_id = run_cmd(cmd, 180)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
