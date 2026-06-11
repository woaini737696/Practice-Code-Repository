#!/usr/bin/env python3
"""上传前端构建产物到服务器（分块上传）"""
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

def get_result(invoke_id, wait=60):
    for _ in range(wait):
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

# 读取构建产物
with open('/tmp/ai-build.tar.gz', 'rb') as f:
    data = f.read()

b64 = base64.b64encode(data).decode('utf-8')
CHUNK_SIZE = 200000  # 200KB per chunk
chunks = [b64[i:i+CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]
print(f"总大小: {len(data)} bytes, 分 {len(chunks)} 块, 每块 ~{CHUNK_SIZE} chars")

# 清理旧文件
run_cmd("rm -f /tmp/ai-build.tar.gz.b64 /tmp/ai-build.tar.gz", 30)
get_result(run_cmd("echo init", 30), wait=10)

# 逐块上传
for i, chunk in enumerate(chunks):
    cmd = f"printf '%s' '{chunk}' >> /tmp/ai-build.tar.gz.b64"
    invoke_id = run_cmd(cmd, 60)
    result = get_result(invoke_id, wait=15)
    if result and result.get('InvocationStatus') == 'Success':
        print(f"  块 {i+1}/{len(chunks)} ✓")
    else:
        status = result.get('InvocationStatus') if result else 'Unknown'
        print(f"  块 {i+1}/{len(chunks)} ✗ ({status})")
        break

# 解码并解压
cmd_final = """#!/bin/bash
set -e
echo "=== 解码并解压 ==="
base64 -d /tmp/ai-build.tar.gz.b64 > /tmp/ai-build.tar.gz 2>/dev/null
rm -f /tmp/ai-build.tar.gz.b64
rm -rf /opt/ai-model-test-platform/frontend/build
mkdir -p /opt/ai-model-test-platform/frontend/build
tar xzf /tmp/ai-build.tar.gz -C /opt/ai-model-test-platform/frontend/build/
rm -f /tmp/ai-build.tar.gz
chmod -R 755 /opt/ai-model-test-platform/frontend/build/
echo "=== 验证 ==="
ls -la /opt/ai-model-test-platform/frontend/build/
ls -la /opt/ai-model-test-platform/frontend/build/static/
echo "UPLOAD_DONE"
"""

print("\n解码并解压...")
invoke_id = run_cmd(cmd_final, 120)
result = get_result(invoke_id, wait=15)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 重启Nginx
cmd_nginx = """#!/bin/bash
set -e
COMPOSE_DIR="/opt/ai-social/deploy"
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
echo "NGINX_RESTARTED"
"""

print("\n重启Nginx...")
invoke_id = run_cmd(cmd_nginx, 120)
result = get_result(invoke_id, wait=15)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 验证
cmd_verify = """#!/bin/bash
echo "========================================"
echo "=== 最终验证 ==="
echo "========================================"
echo "1. 根路径:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/
echo "2. AI-test前端:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/
echo "3. AI-test前端内容:"
curl -s http://localhost/ai-test/ | head -3
echo "4. Health:"
curl -s http://localhost/ai-test/health
echo ""
echo "5. API Root:"
curl -s http://localhost/ai-test/api/
echo ""
echo "6. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/
echo "7. AI数据:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/
echo "========================================"
echo "DONE"
"""

print("\n验证...")
invoke_id = run_cmd(cmd_verify, 120)
result = get_result(invoke_id, wait=15)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")