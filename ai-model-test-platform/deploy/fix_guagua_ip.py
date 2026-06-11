#!/usr/bin/env python3
"""修复Guagua IP配置"""
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

# 从host网络模式的容器测试连接
echo ""
echo "=== 从app-nginx容器测试连接Guagua ==="
docker exec app-nginx sh -c "nc -zv $GUAGUA_FRONTEND_IP 80 2>&1 || echo '无法连接前端'"
docker exec app-nginx sh -c "nc -zv $GUAGUA_BACKEND_IP 8080 2>&1 || echo '无法连接后端'"

echo ""
echo "=== 更新Nginx配置 ==="
mkdir -p $COMPOSE_DIR/nginx

cat > $COMPOSE_DIR/nginx/default.conf << EOF
server {
    listen 80;
    server_name _;

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://127.0.0.1:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://127.0.0.1:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # AI模型测试平台 - /ai-test/
    location /ai-test/ {
        proxy_pass http://127.0.0.1:8000/ai-test/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /ai-test/api/ {
        rewrite ^/ai-test/api/(.*)$ /api/\$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    location /ai-test/ws {
        rewrite ^/ai-test/ws$ /ws break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /ai-test/health {
        rewrite ^/ai-test/health$ /health break;
        proxy_pass http://127.0.0.1:8000;
    }

    # Guagua项目 - 使用Docker容器IP
    location /guagua/ {
        proxy_pass http://$GUAGUA_FRONTEND_IP:80/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /guagua/api/ {
        proxy_pass http://$GUAGUA_BACKEND_IP:8080/api/;
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
EOF

echo ""
echo "=== 重载Nginx配置 ==="
docker exec app-nginx nginx -t && docker exec app-nginx nginx -s reload

echo ""
echo "=== 测试Guagua访问 ==="
curl -s -o /dev/null -w "Guagua状态: %{http_code}\n" http://localhost/guagua/

echo ""
echo "========================================"
echo "所有项目访问地址:"
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

print("修复Guagua IP配置...")
invoke_id = run_cmd(cmd, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
