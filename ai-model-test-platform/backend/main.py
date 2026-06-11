from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.api import distillation, models, tests, scoring, settings
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
