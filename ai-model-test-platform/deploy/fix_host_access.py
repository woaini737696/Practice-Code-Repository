#!/usr/bin/env python3
"""修复Docker容器访问宿主机问题"""
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

# 诊断问题
cmd1 = """#!/bin/bash
set -e

echo "=== 获取宿主机IP ==="
HOST_IP=$(ip route | grep default | awk '{print $3}' | head -1)
echo "默认网关(宿主机IP): $HOST_IP"

echo ""
echo "=== 检查Docker容器内的host.docker.internal ==="
docker exec app-nginx sh -c 'getent hosts host.docker.internal 2>/dev/null || echo "host.docker.internal未解析"'

echo ""
echo "=== 从容器内测试连接宿主机8000端口 ==="
docker exec app-nginx sh -c 'nc -z host.docker.internal 8000 2>/dev/null && echo "host.docker.internal:8000 可连接" || echo "host.docker.internal:8000 不可连接"'

echo ""
echo "=== 从容器内测试连接网关8000端口 ==="
GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
docker exec app-nginx sh -c "nc -z $GATEWAY 8000 2>/dev/null && echo '$GATEWAY:8000 可连接' || echo '$GATEWAY:8000 不可连接'"

echo ""
echo "=== 检查宿主机8000端口监听 ==="
ss -tlnp | grep :8000 || netstat -tlnp | grep :8000 || echo "8000未监听"

echo ""
echo "=== 检查宿主机防火墙 ==="
iptables -L -n | grep 8000 2>/dev/null || echo "无8000相关防火墙规则"
"""

print("[1/3] 诊断连接问题...")
invoke_id = run_cmd(cmd1, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 修复：使用宿主机IP替代host.docker.internal
cmd2 = """#!/bin/bash
set -e

COMPOSE_DIR="/opt/ai-social/deploy"

# 获取宿主机IP（默认网关IP）
HOST_IP=$(ip route | grep default | awk '{print $3}' | head -1)
if [ -z "$HOST_IP" ]; then
    HOST_IP=$(hostname -I | awk '{print $1}')
fi

echo "宿主机IP: $HOST_IP"

echo ""
echo "=== 创建新的Nginx配置（使用宿主机IP） ==="
mkdir -p $COMPOSE_DIR/nginx
cat > $COMPOSE_DIR/nginx/default.conf << NGINXEOF
server {
    listen 80;
    server_name _;

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://$HOST_IP:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://$HOST_IP:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # AI模型测试平台 - /ai-test/
    location /ai-test/ {
        proxy_pass http://$HOST_IP:8000/ai-test/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /ai-test/api/ {
        rewrite ^/ai-test/api/(.*)$ /api/\$1 break;
        proxy_pass http://$HOST_IP:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    location /ai-test/ws {
        rewrite ^/ai-test/ws$ /ws break;
        proxy_pass http://$HOST_IP:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /ai-test/health {
        rewrite ^/ai-test/health$ /health break;
        proxy_pass http://$HOST_IP:8000;
    }

    # Guagua项目 - /guagua/
    location /guagua/ {
        proxy_pass http://guagua-frontend:80/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /guagua/api/ {
        proxy_pass http://guagua-backend:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 根路径项目列表
    location = / {
        return 200 '<!DOCTYPE html><html><head><meta charset="utf-8"><title>服务器项目列表</title></head><body style="font-family:Arial,sans-serif;max-width:800px;margin:50px auto;padding:20px;"><h1>服务器项目列表</h1><ul><li><a href="/ai-data/">AI数据分析中台</a></li><li><a href="/ai-test/">AI模型测试平台</a></li><li><a href="/guagua/">Guagua</a></li></ul></body></html>';
        add_header Content-Type text/html;
    }
}
NGINXEOF

echo ""
echo "=== 停止并重启Nginx容器 ==="
docker stop app-nginx 2>/dev/null || true
docker rm app-nginx 2>/dev/null || true
sleep 2

GUAGUA_NETWORK=$(docker inspect guagua-frontend --format '{{range \$k, \$v := .NetworkSettings.Networks}}{{\$k}}{{end}}' 2>/dev/null || echo "deploy_app-net")

docker run -d \
  --name app-nginx \
  --restart unless-stopped \
  -p 80:80 \
  --network \$GUAGUA_NETWORK \
  -v "$COMPOSE_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:alpine

sleep 3

echo ""
echo "=== 测试Nginx配置 ==="
docker exec app-nginx nginx -t 2>&1 || true
"""

print("\n[2/3] 修复Nginx配置...")
invoke_id = run_cmd(cmd2, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 测试
cmd3 = """#!/bin/bash
set -e

echo "========================================"
echo "最终测试验证"
echo "========================================"

echo ""
echo "1. 根路径:"
curl -s http://localhost/ | head -1

echo ""
echo "2. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "3. AI模型测试平台前端:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/

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
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser11","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "8. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "9. 重定向检查:"
curl -s -L --max-redirs 5 -o /dev/null -w "重定向次数: %{num_redirects}\n" http://localhost/ai-test/health

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

print("\n[3/3] 全面测试...")
invoke_id = run_cmd(cmd3, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
