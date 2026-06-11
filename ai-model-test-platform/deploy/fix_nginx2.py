#!/usr/bin/env python3
"""修复Nginx配置冲突 - 清理端口占用"""
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

# 第一步：强制清理并重启
cmd1 = """#!/bin/bash
set -e

echo "=== 查找占用80端口的进程 ==="
ss -tlnp | grep :80 || netstat -tlnp | grep :80 || echo "无进程占用80"

echo ""
echo "=== 强制停止所有Nginx ==="
killall nginx 2>/dev/null || true
sleep 2

echo ""
echo "=== 检查是否还有Nginx进程 ==="
ps aux | grep nginx | grep -v grep || echo "无Nginx进程"

echo ""
echo "=== 检查sites-enabled ==="
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "无sites-enabled"

echo ""
echo "=== 检查sites-available ==="
ls -la /etc/nginx/sites-available/ 2>/dev/null || echo "无sites-available"

echo ""
echo "=== 检查nginx.conf include ==="
grep -n "include" /etc/nginx/nginx.conf | head -20

echo ""
echo "=== 检查所有conf文件中的server块 ==="
find /etc/nginx/ -name "*.conf" -type f -exec grep -l "server {" {} \; 2>/dev/null
"""

print("[1/4] 诊断问题...")
invoke_id = run_cmd(cmd1, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第二步：清理所有配置并重新创建
cmd2 = """#!/bin/bash
set -e

echo "=== 停止Nginx ==="
systemctl stop nginx 2>/dev/null || true
killall nginx 2>/dev/null || true
sleep 2

echo "=== 清理所有sites-enabled和sites-available ==="
rm -rf /etc/nginx/sites-enabled/*
rm -rf /etc/nginx/sites-available/*

echo "=== 创建统一Nginx配置 ==="
cat > /etc/nginx/sites-available/multi-project << 'NGINXEOF'
server {
    listen 80 default_server;
    server_name _;

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://localhost:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://localhost:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # AI模型测试平台 - /ai-test/
    location /ai-test/ {
        alias /opt/ai-model-test-platform/frontend/;
        index index.html;
        try_files $uri $uri/ /ai-test/index.html;
    }

    location /ai-test/api/ {
        rewrite ^/ai-test/api/(.*)$ /api/$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    location /ai-test/ws {
        rewrite ^/ai-test/ws$ /ws break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ai-test/health {
        rewrite ^/ai-test/health$ /health break;
        proxy_pass http://127.0.0.1:8000;
    }

    # Guagua项目 - /guagua/
    location /guagua/ {
        proxy_pass http://localhost:3000/guagua/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 根路径项目列表
    location = / {
        return 200 '
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>服务器项目列表</title></head>
<body style="font-family:Arial,sans-serif;max-width:800px;margin:50px auto;padding:20px;">
<h1>服务器项目列表</h1>
<ul>
<li><a href="/ai-data/">AI数据分析中台</a></li>
<li><a href="/ai-test/">AI模型测试平台</a></li>
<li><a href="/guagua/">Guagua</a></li>
</ul>
</body>
</html>';
        add_header Content-Type text/html;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/multi-project /etc/nginx/sites-enabled/multi-project

echo "=== 测试配置 ==="
nginx -t

echo "=== 启动Nginx ==="
nginx
sleep 2

echo "=== Nginx进程 ==="
ps aux | grep nginx | grep -v grep

echo "=== 端口监听 ==="
ss -tlnp | grep :80 || echo "80端口未监听"
"""

print("\n[2/4] 清理并重新配置Nginx...")
invoke_id = run_cmd(cmd2, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第三步：检查是否有其他配置覆盖了我们的配置
cmd3 = """#!/bin/bash
set -e

echo "=== 检查nginx.conf完整内容 ==="
cat /etc/nginx/nginx.conf

echo ""
echo "=== 检查所有include的文件 ==="
find /etc/nginx/ -name "*.conf" -type f | while read f; do
    echo "--- $f ---"
    cat "$f"
    echo ""
done
"""

print("\n[3/4] 检查完整Nginx配置...")
invoke_id = run_cmd(cmd3, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第四步：全面测试
cmd4 = """#!/bin/bash
set -e

echo "========================================"
echo "全面测试验证"
echo "========================================"

echo ""
echo "--- 1. 根路径 (项目列表) ---"
curl -s http://localhost/ | head -10

echo ""
echo "--- 2. AI数据分析中台 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "--- 3. AI模型测试平台前端 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/

echo ""
echo "--- 4. AI模型测试平台 Health ---"
curl -s http://localhost/ai-test/health

echo ""
echo "--- 5. AI模型测试平台 API Root ---"
curl -s http://localhost/ai-test/api/

echo ""
echo "--- 6. AI模型测试平台 Models API ---"
curl -s http://localhost/ai-test/api/models

echo ""
echo "--- 7. AI模型测试平台 Auth 注册 (POST) ---"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser3","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "--- 8. Guagua项目 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/ || echo "Guagua未运行"

echo ""
echo "--- 9. Nginx错误日志 ---"
tail -3 /var/log/nginx/error.log 2>/dev/null | grep -v "notice" || echo "无错误"

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

print("\n[4/4] 全面测试...")
invoke_id = run_cmd(cmd4, 120)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
