#!/usr/bin/env python3
"""通过创建detached脚本在服务器上构建"""
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

def get_result(invoke_id, wait=30):
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

# 第一步：创建构建脚本
cmd1 = """#!/bin/bash
cat > /tmp/build_and_deploy.sh << 'SCRIPTEOF'
#!/bin/bash
set -e
LOG=/tmp/build_deploy.log
echo "=== Build started at $(date) ===" > $LOG

# 下载构建产物
echo "Downloading build..." >> $LOG
python3 -c "
import urllib.request, tarfile, os, shutil
url = 'http://115.190.22.21:9999/ai-build.tar.gz'
try:
    urllib.request.urlretrieve(url, '/tmp/ai-build.tar.gz')
    print('Downloaded:', os.path.getsize('/tmp/ai-build.tar.gz'), 'bytes')
except Exception as e:
    print('Download failed:', e)
    # Fallback: build from source
    print('Falling back to source build...')
    import subprocess
    os.chdir('/opt/ai-model-test-platform/frontend')
    subprocess.run(['npm', 'install', '--legacy-peer-deps'], check=True)
    subprocess.run(['npm', 'run', 'build'], check=True, env={'CI': 'false', 'PATH': os.environ.get('PATH', '')})
" >> $LOG 2>&1

# 解压如果下载成功
if [ -f /tmp/ai-build.tar.gz ]; then
    echo "Extracting..." >> $LOG
    rm -rf /opt/ai-model-test-platform/frontend/build
    mkdir -p /opt/ai-model-test-platform/frontend/build
    tar xzf /tmp/ai-build.tar.gz -C /opt/ai-model-test-platform/frontend/build/ 2>> $LOG
    rm -f /tmp/ai-build.tar.gz
fi

# 修复权限
chmod -R 755 /opt/ai-model-test-platform/frontend/build/ 2>> $LOG

# 重启Nginx
echo "Restarting Nginx..." >> $LOG
docker stop app-nginx 2>/dev/null || true
docker rm app-nginx 2>/dev/null || true
sleep 2

docker run -d \
  --name app-nginx \
  --restart unless-stopped \
  --network host \
  --user root \
  -v "/opt/ai-social/deploy/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  -v "/opt/ai-model-test-platform/frontend/build:/opt/ai-model-test-platform/frontend/build:ro" \
  nginx:alpine >> $LOG 2>&1

sleep 3
echo "=== Build done at $(date) ===" >> $LOG
echo "DONE" > /tmp/build_status.txt
SCRIPTEOF

chmod +x /tmp/build_and_deploy.sh
echo "Script created"
"""

print("[1] 创建构建脚本...")
invoke_id = run_cmd(cmd1, 60)
result = get_result(invoke_id, wait=10)
if result:
    print(f"状态: {result.get('InvocationStatus')}")

# 第二步：后台执行脚本
cmd2 = """#!/bin/bash
nohup /tmp/build_and_deploy.sh > /dev/null 2>&1 &
echo "Build started in background, PID=$!"
"""

print("\n[2] 启动后台构建...")
invoke_id = run_cmd(cmd2, 60)
result = get_result(invoke_id, wait=10)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")

# 等待并检查
for attempt in range(10):
    print(f"\n[3.{attempt+1}] 等待30秒后检查...")
    time.sleep(30)
    
    cmd3 = """#!/bin/bash
echo "=== Build status ==="
cat /tmp/build_status.txt 2>/dev/null || echo "Not done"
echo ""
echo "=== Build log tail ==="
tail -5 /tmp/build_deploy.log 2>/dev/null || echo "No log"
echo ""
echo "=== Build files ==="
ls -la /opt/ai-model-test-platform/frontend/build/static/ 2>/dev/null || echo "No build files"
"""
    
    invoke_id = run_cmd(cmd3, 60)
    result = get_result(invoke_id, wait=10)
    if result and result.get('InvocationStatus') == 'Success':
        output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
        print(f"输出:\n{output}")
        if "DONE" in output:
            print("✅ 构建完成！")
            break
    else:
        print("检查失败")

# 第四步：验证
print("\n[4] 最终验证...")
cmd4 = """#!/bin/bash
echo "=== 验证 ==="
echo "1. 根路径:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/
echo "2. AI-test:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-test/
echo "3. AI-test内容:"
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
echo ""
echo "========================================"
echo "访问地址:"
echo "  http://47.112.170.125/           - 项目列表"
echo "  http://47.112.170.125/ai-test/   - AI模型测试平台"
echo "  http://47.112.170.125/guagua/    - Guagua"
echo "  http://47.112.170.125/ai-data/   - AI数据分析中台"
echo "========================================"
"""

invoke_id = run_cmd(cmd4, 60)
result = get_result(invoke_id, wait=15)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")