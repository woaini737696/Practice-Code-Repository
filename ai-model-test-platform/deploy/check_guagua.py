#!/usr/bin/env python3
"""检查并修复Guagua容器"""
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

echo "=== 检查所有Docker容器 ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.State}}"

echo ""
echo "=== 检查Guagua容器日志 ==="
docker logs guagua-frontend --tail 5 2>/dev/null || echo "无法获取guagua-frontend日志"
docker logs guagua-backend --tail 5 2>/dev/null || echo "无法获取guagua-backend日志"

echo ""
echo "=== 检查Docker网络 ==="
docker network inspect deploy_app-net 2>/dev/null | grep -E "Containers|IPv4Address" | head -20 || echo "无法获取网络信息"

echo ""
echo "=== 尝试启动Guagua容器 ==="
docker start guagua-frontend 2>/dev/null || echo "无法启动guagua-frontend"
docker start guagua-backend 2>/dev/null || echo "无法启动guagua-backend"
docker start app-nginx 2>/dev/null || echo "无法启动app-nginx"

sleep 3

echo ""
echo "=== 再次检查容器状态 ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== 获取Guagua容器IP ==="
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
echo "Guagua前端IP: $GUAGUA_FRONTEND_IP"
echo "Guagua后端IP: $GUAGUA_BACKEND_IP"

echo ""
echo "=== 测试从宿主机访问Guagua ==="
if [ -n "$GUAGUA_FRONTEND_IP" ]; then
    curl -s -o /dev/null -w "从前端IP访问: %{http_code}\n" http://$GUAGUA_FRONTEND_IP:80/ 2>/dev/null || echo "无法从前端IP访问"
fi
"""

print("检查Guagua容器状态...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
