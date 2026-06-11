from typing import List, Dict
from fastapi import WebSocket
import json


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃的WebSocket连接
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_test_progress(self, test_id: int, progress: int, status: str):
        """广播测试进度"""
        await self.broadcast({
            "type": "test_progress",
            "test_id": test_id,
            "progress": progress,
            "status": status
        })


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()
