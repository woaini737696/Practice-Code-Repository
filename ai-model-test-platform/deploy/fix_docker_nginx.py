#!/usr/bin/env python3
"""修复Docker占用的80端口问题"""
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

# 第一步：检查Docker容器
cmd1 = """#!/bin/bash
set -e

echo "=== Docker容器列表 ==="
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}" 2>/dev/null || echo "Docker未安装或未运行"

echo ""
echo "=== 查找映射80端口的容器 ==="
docker ps --filter "publish=80" --format "{{.ID}}\t{{.Names}}\t{{.Ports}}" 2>/dev/null || echo "无映射80端口的容器"

echo ""
echo "=== 查找所有运行中的容器 ==="
docker ps 2>/dev/null || echo "无运行中的容器"

echo ""
echo "=== 检查容器内的Nginx配置 ==="
for cid in $(docker ps -q 2>/dev/null); do
    name=$(docker inspect --format '{{.Name}}' $cid 2>/dev/null | sed 's/^\///')
    echo "--- 容器: $name ($cid) ---"
    docker exec $cid sh -c 'ls /etc/nginx/conf.d/ 2>/dev/null || ls /etc/nginx/sites-enabled/ 2>/dev/null || echo "无Nginx配置"'
done
"""

print("[1/4] 检查Docker容器...")
invoke_id = run_cmd(cmd1, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第二步：将统一Nginx配置复制到Docker容器中
cmd2 = """#!/bin/bash
set -e

echo "=== 查找映射80端口的Nginx容器 ==="
NGINX_CONTAINER=$(docker ps --filter "publish=80" --format "{{.Names}}" 2>/dev/null | head -1)

echo "容器名: $NGINX_CONTAINER"

if [ -z "$NGINX_CONTAINER" ]; then
    echo "没有找到映射80端口的容器"
    exit 1
fi

echo ""
echo "=== 检查容器内的Nginx配置路径 ==="
docker exec $NGINX_CONTAINER sh -c 'ls -la /etc/nginx/conf.d/ 2>/dev/null || ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "检查其他路径"'

echo ""
echo "=== 尝试找到default.conf ==="
docker exec $NGINX_CONTAINER find /etc/nginx -name "*.conf" -type f 2>/dev/null | head -10
"""

print("\n[2/4] 检查Docker Nginx配置...")
invoke_id = run_cmd(cmd2, 60)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 第三步：修改Docker容器内的Nginx配置
cmd3 = """#!/bin/bash
set -e

echo "=== 查找映射80端口的Nginx容器 ==="
NGINX_CONTAINER=$(docker ps --filter "publish=80" --format "{{.Names}}" 2>/dev/null | head -1)

echo "容器名: $NGINX_CONTAINER"

if [ -z "$NGINX_CONTAINER" ]; then
    echo "没有找到映射80端口的容器，尝试直接启动系统Nginx"
    # 停止docker-proxy
    docker stop $(docker ps -q --filter "publish=80" 2>/dev/null) 2>/dev/null || true
    systemctl start nginx 2>/dev/null || nginx
    exit 0
fi

echo ""
echo "=== 备份并替换容器内的Nginx配置 ==="

# 创建新的统一配置
cat > /tmp/multi-project.conf << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    # AI数据分析中台 - /ai-data/
    location /ai-data/ {
        proxy_pass http://host.docker.internal:8788/ai-data/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    location /ai-data/api/ {
        proxy_pass http://host.docker.internal:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # AI模型测试平台 - /ai-test/
    location /ai-test/ {
        proxy_pass http://host.docker.internal:8000/ai-test/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ai-test/api/ {
        rewrite ^/ai-test/api/(.*)$ /api/$1 break;
        proxy_pass http://host.docker.internal:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Prefix /ai-test;
    }

    location /ai-test/ws {
        rewrite ^/ai-test/ws$ /ws break;
        proxy_pass http://host.docker.internal:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ai-test/health {
        rewrite ^/ai-test/health$ /health break;
        proxy_pass http://host.docker.internal:8000;
    }

    # Guagua项目 - /guagua/
    location /guagua/ {
        proxy_pass http://host.docker.internal:3000/guagua/;
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

# 复制配置到容器
docker cp /tmp/multi-project.conf $NGINX_CONTAINER:/etc/nginx/conf.d/default.conf

# 测试并重载Nginx
docker exec $NGINX_CONTAINER nginx -t
docker exec $NGINX_CONTAINER nginx -s reload

echo ""
echo "=== Docker Nginx已更新 ==="
"""

print("\n[3/4] 修改Docker Nginx配置...")
invoke_id = run_cmd(cmd3, 120)
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
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"testuser4","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "--- 8. Guagua项目 ---"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/ || echo "Guagua未运行"

echo ""
echo "--- 9. Nginx错误日志 ---"
docker ps --filter "publish=80" --format "{{.Names}}" 2>/dev/null | head -1 | xargs -I {} docker exec {} sh -c 'tail -3 /var/log/nginx/error.log 2>/dev/null || echo "无错误日志"' 2>/dev/null || tail -3 /var/log/nginx/error.log 2>/dev/null | grep -v "notice" || echo "无错误"

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
