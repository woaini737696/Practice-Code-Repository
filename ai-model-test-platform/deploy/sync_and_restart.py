#!/usr/bin/env python3
"""同步代码到服务器并重启"""
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

echo "=== 1. 停止旧的后端服务 ==="
ps aux | grep "uvicorn" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 2

echo ""
echo "=== 2. 直接修改服务器上的main.py（移除root_path） ==="
cat > /opt/ai-model-test-platform/backend/main.py << 'PYEOF'
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.api import distillation, models, tests, scoring, settings, auth
from app.websocket.manager import websocket_manager

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Model Test Platform",
    description="AI聊天模型测试平台",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(auth.router)
app.include_router(distillation.router)
app.include_router(models.router)
app.include_router(tests.router)
app.include_router(scoring.router)
app.include_router(settings.router)


@app.get("/")
def root():
    return {"message": "AI Model Test Platform API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息（可选，用于心跳检测等）
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
PYEOF

echo ""
echo "=== 3. 验证修改 ==="
grep -n "root_path" /opt/ai-model-test-platform/backend/main.py || echo "✅ root_path已移除"

echo ""
echo "=== 4. 启动后端服务 ==="
cd /opt/ai-model-test-platform/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 > /opt/ai-model-test-platform/backend/uvicorn.log 2>&1 &
sleep 3

echo ""
echo "=== 5. 检查后端进程 ==="
ps aux | grep uvicorn | grep -v grep || echo "后端未启动"

echo ""
echo "========================================"
echo "全面测试验证"
echo "========================================"

echo ""
echo "1. 根路径:"
ROOT=$(curl -s http://localhost/)
if echo "$ROOT" | grep -q "AI模型测试平台"; then
    echo "✅ 根路径正常"
else
    echo "❌ 根路径异常"
fi

echo ""
echo "2. AI模型测试平台前端:"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ai-test/)
if [ "$CODE" = "200" ]; then
    echo "✅ 前端正常 (200)"
else
    echo "❌ 前端异常 ($CODE)"
fi

echo ""
echo "3. API Root (直接访问后端):"
curl -s http://localhost:8000/

echo ""
echo "4. API Root (通过Nginx):"
API_ROOT=$(curl -s http://localhost/ai-test/api/)
echo "$API_ROOT"
if echo "$API_ROOT" | grep -q "AI Model Test Platform"; then
    echo "✅ API Root正常"
else
    echo "❌ API Root异常"
fi

echo ""
echo "5. Models API:"
MODELS=$(curl -s http://localhost/ai-test/api/models)
echo "$MODELS"
if echo "$MODELS" | grep -q "\[\]"; then
    echo "✅ Models API正常"
else
    echo "❌ Models API异常"
fi

echo ""
echo "6. Health:"
curl -s http://localhost/ai-test/health

echo ""
echo "7. Auth注册:"
curl -s -X POST -H "Content-Type: application/json" -d '{"username":"finaltest3","password":"testpass123"}' http://localhost/ai-test/api/auth/register

echo ""
echo "8. Auth登录:"
LOGIN=$(curl -s -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=finaltest3&password=testpass123" http://localhost/ai-test/api/auth/login)
if echo "$LOGIN" | grep -q "access_token"; then
    echo "✅ 登录正常"
else
    echo "❌ 登录异常: $LOGIN"
fi

echo ""
echo "9. Guagua:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/guagua/

echo ""
echo "10. AI数据分析中台:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ai-data/

echo ""
echo "11. 重定向循环检查:"
REDIRECTS=$(curl -s -L --max-redirs 10 -o /dev/null -w "%{num_redirects}" http://localhost/ai-test/health)
if [ "$REDIRECTS" = "0" ]; then
    echo "✅ 无重定向循环"
else
    echo "❌ 重定向次数: $REDIRECTS"
fi

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
echo "默认账号: admin"
echo "默认密码: admin123"
echo "========================================"
"""

print("同步代码并重启服务...")
invoke_id = run_cmd(cmd, 180)
result = get_result(invoke_id)
if result:
    print(f"状态: {result.get('InvocationStatus')}")
    output = base64.b64decode(result.get('Output', '')).decode('utf-8', errors='replace')
    print(f"输出:\n{output}")
