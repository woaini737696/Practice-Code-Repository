#!/usr/bin/env python3
"""后台构建前端并循环检查"""
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

# 第一步：后台启动构建
cmd1 = """#!/bin/bash
cd /opt/ai-model-test-platform/frontend
rm -rf build node_modules
# 后台运行构建
nohup bash -c 'cd /opt/ai-model-test-platform/frontend && npm install --legacy-peer-deps 2>&1 && CI=false npm run build 2>&1 && echo BUILD_SUCCESS > /tmp/build_status.txt' > /tmp/build_output.log 2>&1 &
echo "Build started, PID=$!"
"""

print("[1] 启动后台构建...")
invoke_id = run_cmd(cmd1, 3600)
result = get_result(invoke_id, wait=10)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 循环检查构建状态
for attempt in range(12):
    print(f"\n[2.{attempt+1}] 等待30秒后检查...")
    time.sleep(30)
    
    cmd2 = """#!/bin/bash
echo "=== Build process ==="
ps aux | grep -E "npm|node" | grep -v grep | head -3 || echo "No build process"
echo ""
echo "=== Build status file ==="
cat /tmp/build_status.txt 2>/dev/null || echo "Not done yet"
echo ""
echo "=== Build output ==="
ls -la /opt/ai-model-test-platform/frontend/build/ 2>/dev/null | head -5 || echo "No build dir"
echo ""
echo "=== Build log tail ==="
tail -5 /tmp/build_output.log 2>/dev/null || echo "No log"
"""
    
    invoke_id = run_cmd(cmd2, 60)
    result = get_result(invoke_id, wait=10)
    if result:
        output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
        print(f"输出:\n{output}")
        
        if "BUILD_SUCCESS" in output:
            print("✅ 构建成功！")
            break
        elif "No build process" in output and "Not done yet" in output:
            print("构建可能已完成，但状态文件未更新")
            break
    else:
        print("检查失败")

# 第三步：重启Nginx
print("\n[3] 重启Nginx...")
cmd3 = """#!/bin/bash
set -e
COMPOSE_DIR="/opt/ai-social/deploy"
chmod -R 755 /opt/ai-model-test-platform/frontend/build/ 2>/dev/null || true
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
echo "=== 验证 ==="
echo "1. 根路径:"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/
echo "2. AI-test:"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/ai-test/
echo "3. Health:"
curl -s http://localhost/ai-test/health
echo ""
echo "4. Guagua:"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/guagua/
echo "5. AI数据:"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/ai-data/
echo "DONE"
"""

invoke_id = run_cmd(cmd3, 120)
result = get_result(invoke_id, wait=15)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")