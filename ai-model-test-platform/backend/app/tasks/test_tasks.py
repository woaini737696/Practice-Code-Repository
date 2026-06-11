import asyncio
from app.tasks.celery_app import celery_app
from app.core.test_engine import TestEngine
from app.websocket.manager import websocket_manager


@celery_app.task(bind=True)
def run_test_task(self, test_id: int):
    """Celery任务：运行测试"""
    
    async def progress_callback(test_id, progress, status):
        """进度回调，通过WebSocket推送"""
        await websocket_manager.broadcast_test_progress(test_id, progress, status)
    
    async def run():
        engine = TestEngine()
        await engine.run_test(test_id, progress_callback=progress_callback)
    
    # 运行异步任务
    asyncio.run(run())
    
    return {"test_id": test_id, "status": "completed"}
