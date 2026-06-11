#!/usr/bin/env python3
"""步骤2: 上传项目代码文件"""
import json
import time
import os
import base64
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

client = AcsClient('ALIBABA_CLOUD_ACCESS_KEY_ID', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'cn-shenzhen')
INSTANCE_ID = 'i-wz9egw4g1k2w0ml1hoy0'
BASE = '/workspace/ai-model-test-platform'

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
        time.sleep(3)
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

def upload_file(local_path, remote_path):
    """上传单个文件"""
    with open(local_path, 'r') as f:
        content = f.read()

    b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
    chunk_size = 12000

    if len(b64) <= chunk_size:
        cmd = f"echo '{b64}' | base64 -d > {remote_path}"
        invoke_id = run_cmd(cmd, 60)
        result = get_result(invoke_id)
        return result and result.get('InvocationStatus') == 'Success'
    else:
        chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]
        cmd = f"> {remote_path}"
        invoke_id = run_cmd(cmd, 30)
        get_result(invoke_id)

        for chunk in chunks:
            cmd = f"echo '{chunk}' | base64 -d >> {remote_path}"
            invoke_id = run_cmd(cmd, 60)
            result = get_result(invoke_id)
            if not result or result.get('InvocationStatus') != 'Success':
                return False
        return True

files = [
    'backend/requirements.txt',
    'backend/main.py',
    'backend/Dockerfile.prod',
    'backend/app/__init__.py',
    'backend/app/config.py',
    'backend/app/database.py',
    'backend/app/api/__init__.py',
    'backend/app/api/auth.py',
    'backend/app/api/models.py',
    'backend/app/api/tests.py',
    'backend/app/api/distillation.py',
    'backend/app/api/scoring.py',
    'backend/app/api/settings.py',
    'backend/app/models/__init__.py',
    'backend/app/models/user.py',
    'backend/app/models/ai_model.py',
    'backend/app/models/test.py',
    'backend/app/models/test_result.py',
    'backend/app/models/distilled_user.py',
    'backend/app/models/chat_record.py',
    'backend/app/models/score_dimension.py',
    'backend/app/models/annotation.py',
    'backend/app/models/system_config.py',
    'backend/app/schemas/__init__.py',
    'backend/app/core/model_gateway.py',
    'backend/app/core/test_engine.py',
    'backend/app/core/report_generator.py',
    'backend/app/services/__init__.py',
    'backend/app/services/email_service.py',
    'backend/app/tasks/__init__.py',
    'backend/app/tasks/celery_app.py',
    'backend/app/tasks/test_tasks.py',
    'backend/app/websocket/__init__.py',
    'backend/app/websocket/manager.py',
    'frontend/package.json',
    'frontend/tsconfig.json',
    'frontend/Dockerfile.prod',
    'frontend/nginx.conf',
    'frontend/public/index.html',
    'frontend/public/manifest.json',
    'frontend/src/index.tsx',
    'frontend/src/App.tsx',
    'frontend/src/App.css',
    'frontend/src/index.css',
    'frontend/src/services/api.ts',
    'frontend/src/services/websocket.ts',
    'frontend/src/pages/auth/LoginPage.tsx',
    'frontend/src/pages/tests/TestList.tsx',
    'frontend/src/pages/tests/TestDetail.tsx',
    'frontend/src/pages/models/ModelList.tsx',
    'frontend/src/pages/models/ModelDetail.tsx',
    'frontend/src/pages/distillation/DistillationList.tsx',
    'frontend/src/pages/distillation/DistillationDetail.tsx',
    'frontend/src/pages/scoring/ScoringList.tsx',
    'frontend/src/pages/settings/SettingsPage.tsx',
    'docker-compose.prod.yml',
]

print("[2/3] 上传项目文件...")
success = 0
for i, rel_path in enumerate(files):
    local_path = os.path.join(BASE, rel_path)
    remote_path = f"/opt/ai-model-test-platform/{rel_path}"
    if not os.path.exists(local_path):
        continue
    if upload_file(local_path, remote_path):
        success += 1
        print(f"  [{i+1}/{len(files)}] ✓ {rel_path}")
    else:
        print(f"  [{i+1}/{len(files)}] ✗ {rel_path}")

print(f"\n上传完成: {success}/{len(files)} 个文件")
