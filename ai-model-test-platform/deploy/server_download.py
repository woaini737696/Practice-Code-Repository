#!/usr/bin/env python3
"""通过服务器端Python脚本下载构建产物"""
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

# 在服务器上运行Python脚本下载构建产物
cmd = """#!/bin/bash
python3 -c "
import urllib.request, tarfile, os, shutil, subprocess

print('=== 下载构建产物 ===')
url = 'http://115.190.22.21:9999/ai-build.tar.gz'
try:
    urllib.request.urlretrieve(url, '/tmp/ai-build.tar.gz')
    print('下载完成')
    print('文件大小:', os.path.getsize('/tmp/ai-build.tar.gz'))
    
    print('=== 解压 ===')
    build_dir = '/opt/ai-model-test-platform/frontend/build'
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    with tarfile.open('/tmp/ai-build.tar.gz', 'r:gz') as tar:
        tar.extractall(path=build_dir)
    os.remove('/tmp/ai-build.tar.gz')
    
    print('=== 修复权限 ===')
    os.chmod(build_dir, 0o755)
    for root, dirs, files in os.walk(build_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o644)
    
    print('=== 验证 ===')
    for f in os.listdir(build_dir):
        print(' ', f)
    
    print('=== 重启Nginx ===')
    subprocess.run(['docker', 'stop', 'app-nginx'], capture_output=True)
    subprocess.run(['docker', 'rm', 'app-nginx'], capture_output=True)
    subprocess.run([
        'docker', 'run', '-d',
        '--name', 'app-nginx',
        '--restart', 'unless-stopped',
        '--network', 'host',
        '--user', 'root',
        '-v', '/opt/ai-social/deploy/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro',
        '-v', '/opt/ai-model-test-platform/frontend/build:/opt/ai-model-test-platform/frontend/build:ro',
        'nginx:alpine'
    ], capture_output=True)
    import time
    time.sleep(3)
    
    print('=== 测试验证 ===')
    import urllib.request
    for path in ['/', '/ai-test/', '/ai-test/health', '/ai-test/api/', '/guagua/', '/ai-data/']:
        try:
            req = urllib.request.Request('http://localhost' + path)
            resp = urllib.request.urlopen(req, timeout=5)
            print(f'  {path}: {resp.status}')
        except Exception as e:
            print(f'  {path}: ERROR - {e}')
    
    print('ALL_DONE')
except Exception as e:
    print(f'ERROR: {e}')
"
"""

print("在服务器上下载构建产物...")
invoke_id = run_cmd(cmd, 300)
result = get_result(invoke_id, wait=60)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")