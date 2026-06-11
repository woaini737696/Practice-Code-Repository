#!/usr/bin/env python3
"""修复Guagua访问问题"""
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

# 检查Guagua容器网络和端口
cmd1 = """#!/bin/bash
set -e

echo "=== Guagua容器信息 ==="
docker inspect guagua-frontend --format '{{range \$k, \$v := .NetworkSettings.Networks}}{{\$k}}: {{\$v.IPAddress}}{{end}}' 2>/dev/null || echo "无法获取"

echo ""
echo "=== Guagua端口映射 ==="
docker inspect guagua-frontend --format '{{json .NetworkSettings.Ports}}' 2>/dev/null || echo "无端口映射"

echo ""
echo "=== Guagua后端端口映射 ==="
docker inspect guagua-backend --format '{{json .NetworkSettings.Ports}}' 2>/dev/null || echo "无端口映射"

echo ""
echo "=== 测试从宿主机访问Guagua ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null || echo "3000端口未响应"
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "127.0.0.1:3000未响应"

echo ""
echo "=== 获取Guagua容器IP ==="
GUAGUA_IP=$(docker inspect guagua-frontend --format '{{range \$k, \$v := .NetworkSettings.Networks}}{{\$v.IPAddress}}{{end}}' 2>/dev/null || echo "")
echo "Guagua前端IP: $GUAGUA_IP"

GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range \$k, \$v := .NetworkSettings.Networks}}{{\$v.IPAddress}}{{end}}' 2>/dev/null || echo "")
echo "Guagua后端IP: $GUAGUA_BACKEND_IP"
"""

print("[1/3] 检查Guagua网络...")
invoke_id = run_cmd(cmd1, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 修复Nginx配置，使用Guagua容器IP
cmd2 = """#!/bin/bash
set -e

COMPOSE_DIR="/opt/ai-social/deploy"

# 获取Guagua容器IP
GUAGUA_FRONTEND_IP=$(docker inspect guagua-frontend --format '{{range \$k, \$v := .NetworkSettings.Networks}}{{\$v.IPAddress}}{{end}}' 2>/dev/null || echo "")
GUAGUA_BACKEND_IP=$(docker inspect guagua-backend --format '{{range \$k, \$v := .NetworkSettings.Networks}}{{\$v.IPAddress}}{{end}}' 2>/dev/null || echo "")

echo "Guagua前端IP: $GUAGUA_FRONTEND_IP"
echo "Guagua后端IP: $GUAGUA_BACKEND_IP"

# 如果无法获取IP，使用docker0网关IP
if [ -z "$GUAGUA_FRONTEND_IP" ]; then
    GUAGUA_FRONTEND_IP="172.18.0.3"
    echo "使用默认前端IP: $GUAGUA_FRONTEND_IP"
fi
if [ -z "$GUAGUA_BACKEND_IP" ]; then
    GUAGUA_BACKEND_IP="172.18.0.4"
    echo "使用默认后端IP: $GUAGUA_BACKEND_IP"
fi

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
echo "=== 完成 ==="
"""

print("\n[2/3] 修复Guagua配置...")
invoke_id = run_cmd(cmd2, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 最终测试
cmd3 = """#!/bin/bash
set -e

echo "========================================"
echo "最终验证测试"
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
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser14","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "8. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "9. 重定向检查:"
curl -s -L --max-redirs 5 -o /dev/null -w "重定向次数: %{num_redirects}\n" http://localhost/ai-test/health

echo ""
echo "10. Nginx错误日志:"
docker exec app-nginx sh -c 'tail -3 /var/log/nginx/error.log 2>/dev/null || echo "无错误"'

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

print("\n[3/3] 最终测试...")
invoke_id = run_cmd(cmd3, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
