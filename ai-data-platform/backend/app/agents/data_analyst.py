import json
import logging
import re
from typing import Dict, Any, List, Optional
from app.services.mysql_service import mysql_service

logger = logging.getLogger(__name__)


class DataAnalystAgent:
    """AI数据分析Agent - 简化版，不依赖外部LLM库"""

    def __init__(self):
        self.schema_info = None

    async def _get_schema_context(self) -> str:
        """获取数据库schema上下文"""
        if self.schema_info is None:
            result = await mysql_service.get_schema()
            if result["success"]:
                self.schema_info = result["tables"]
            else:
                return "无法获取数据库结构"

        context = "数据库表结构:\n"
        for table in self.schema_info[:20]:
            context += f"\n表名: {table['table_name']}"
            if table.get('table_comment'):
                context += f" ({table['table_comment']})"
            context += "\n字段:\n"
            for col in table.get('columns', []):
                comment = f" - {col['comment']}" if col.get('comment') else ""
                context += f"  - {col['name']} ({col['type']}){comment}\n"
        return context

    def _generate_mock_sql(self, message: str) -> str:
        """根据用户消息生成模拟SQL（演示用）"""
        msg = message.lower()

        if "用户" in message or "user" in msg:
            if "最近" in message or "7天" in message or "近7" in message:
                return "SELECT DATE(created_at) as date, COUNT(*) as new_users FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY DATE(created_at) ORDER BY date DESC"
            elif "今天" in message or "今日" in message:
                return "SELECT COUNT(*) as today_users FROM users WHERE DATE(created_at) = CURDATE()"
            elif "活跃" in message:
                return "SELECT DATE(last_active) as date, COUNT(*) as active_users FROM users WHERE last_active >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY DATE(last_active) ORDER BY date DESC"
            else:
                return "SELECT COUNT(*) as total_users FROM users"

        if "订单" in message or "order" in msg:
            if "最近" in message or "7天" in message:
                return "SELECT DATE(created_at) as date, COUNT(*) as order_count, SUM(amount) as total_amount FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY DATE(created_at) ORDER BY date DESC"
            else:
                return "SELECT COUNT(*) as total_orders, SUM(amount) as total_amount FROM orders"

        if "收入" in message or "金额" in message or "revenue" in msg:
            return "SELECT DATE(created_at) as date, SUM(amount) as daily_revenue FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY DATE(created_at) ORDER BY date DESC"

        if "注册" in message:
            return "SELECT DATE(created_at) as date, COUNT(*) as registrations FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY DATE(created_at) ORDER BY date DESC"

        # 默认SQL
        return "SHOW TABLES"

    def _generate_mock_analysis(self, message: str, result: Dict) -> str:
        """生成模拟分析结果"""
        row_count = result.get("row_count", 0)
        data = result.get("data", [])

        if row_count == 0:
            return "查询成功，但没有返回数据。可能是当前数据库中没有数据，或者查询条件不匹配。"

        # 尝试提取关键数字
        summary = []
        if data:
            first_row = data[0]
            for key, value in first_row.items():
                if isinstance(value, (int, float)) and value > 0:
                    summary.append(f"{key}: {value}")

        if summary:
            return f"查询成功！返回了 {row_count} 条数据。关键指标：{', '.join(summary[:3])}。从数据趋势来看，业务运行平稳，建议持续关注后续变化。"
        else:
            return f"查询成功！返回了 {row_count} 条数据。数据已展示在下方表格中，你可以进一步询问具体的分析方向。"

    async def chat(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        主对话接口
        """
        # 生成SQL
        sql = self._generate_mock_sql(message)
        logger.info(f"生成的SQL: {sql}")

        # 执行查询
        result = await mysql_service.execute_query(sql)

        if result["success"]:
            analysis = self._generate_mock_analysis(message, result)
            return {
                "type": "data",
                "sql": sql,
                "data": result.get("data", []),
                "columns": result.get("columns", []),
                "row_count": result.get("row_count", 0),
                "execution_time": result.get("execution_time", 0),
                "analysis": analysis,
                "suggestions": [
                    "按时间趋势查看",
                    "按渠道/维度拆分",
                    "对比历史数据",
                    "查看详细数据"
                ]
            }
        else:
            # 查询失败，返回模拟数据
            return {
                "type": "text",
                "sql": sql,
                "analysis": f"SQL查询执行失败: {result.get('error', '未知错误')}。当前可能是开发环境，数据库尚未连接。",
                "suggestions": [
                    "检查数据库连接配置",
                    "查看数据库表结构",
                    "尝试其他查询"
                ]
            }


# 全局Agent实例
agent = DataAnalystAgent()
