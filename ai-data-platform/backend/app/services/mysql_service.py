import aiomysql
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.security import validate_read_only, sanitize_sql, mask_phone_in_data
import logging

logger = logging.getLogger(__name__)


class MySQLService:
    """MySQL只读查询服务"""

    def __init__(self):
        self.pool = None

    async def connect(self):
        """创建连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DATABASE,
                minsize=1,
                maxsize=10,
                autocommit=True,
                read_default_file=None,
                # 只读模式设置
                init_command="SET SESSION TRANSACTION READ ONLY"
            )
            logger.info(f"MySQL连接池创建成功: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            raise

    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL连接池已关闭")

    async def execute_query(
        self,
        sql: str,
        params: Optional[tuple] = None,
        apply_mask: bool = True
    ) -> Dict[str, Any]:
        """
        执行只读查询

        Args:
            sql: SQL查询语句
            params: 查询参数
            apply_mask: 是否对结果进行手机号脱敏

        Returns:
            {
                "success": bool,
                "data": List[Dict],
                "columns": List[str],
                "row_count": int,
                "execution_time": float,
                "error": str (如果失败)
            }
        """
        # 1. 清理SQL
        try:
            sql = sanitize_sql(sql)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # 2. 安全验证
        is_valid, error_msg = validate_read_only(sql)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # 3. 检查连接
        if not self.pool:
            await self.connect()

        start_time = asyncio.get_event_loop().time()

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # 设置超时
                    await cur.execute(f"SET SESSION MAX_EXECUTION_TIME={settings.MAX_QUERY_TIMEOUT * 1000}")

                    # 执行查询
                    await cur.execute(sql, params)

                    # 获取结果
                    rows = await cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []

                    # 限制返回行数
                    if len(rows) > settings.MAX_QUERY_ROWS:
                        rows = rows[:settings.MAX_QUERY_ROWS]

                    execution_time = asyncio.get_event_loop().time() - start_time

                    # 转换结果为字典列表
                    data = []
                    for row in rows:
                        row_dict = {}
                        for key, value in row.items():
                            # 处理日期时间类型
                            if hasattr(value, 'isoformat'):
                                row_dict[key] = value.isoformat()
                            else:
                                row_dict[key] = value
                        data.append(row_dict)

                    # 手机号脱敏
                    if apply_mask:
                        data = mask_phone_in_data(data)

                    return {
                        "success": True,
                        "data": data,
                        "columns": columns,
                        "row_count": len(data),
                        "execution_time": round(execution_time, 3),
                        "sql": sql
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"查询超时，超过{settings.MAX_QUERY_TIMEOUT}秒限制",
                "execution_time": settings.MAX_QUERY_TIMEOUT
            }
        except Exception as e:
            logger.error(f"查询执行错误: {e}, SQL: {sql}")
            return {
                "success": False,
                "error": f"查询执行失败: {str(e)}"
            }

    async def get_schema(self) -> Dict[str, Any]:
        """
        获取数据库表结构信息
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # 获取所有表
                    await cur.execute("""
                        SELECT TABLE_NAME, TABLE_COMMENT
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = %s
                        ORDER BY TABLE_NAME
                    """, (settings.MYSQL_DATABASE,))

                    tables = await cur.fetchall()

                    schema_info = []
                    for table in tables:
                        table_name = table['TABLE_NAME']
                        table_comment = table['TABLE_COMMENT']

                        # 获取表字段
                        await cur.execute("""
                            SELECT
                                COLUMN_NAME,
                                DATA_TYPE,
                                COLUMN_COMMENT,
                                IS_NULLABLE,
                                COLUMN_DEFAULT
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                            ORDER BY ORDINAL_POSITION
                        """, (settings.MYSQL_DATABASE, table_name))

                        columns = await cur.fetchall()

                        schema_info.append({
                            "table_name": table_name,
                            "table_comment": table_comment,
                            "columns": [
                                {
                                    "name": col['COLUMN_NAME'],
                                    "type": col['DATA_TYPE'],
                                    "comment": col['COLUMN_COMMENT'],
                                    "nullable": col['IS_NULLABLE'] == 'YES',
                                    "default": col['COLUMN_DEFAULT']
                                }
                                for col in columns
                            ]
                        })

                    return {
                        "success": True,
                        "database": settings.MYSQL_DATABASE,
                        "tables": schema_info,
                        "table_count": len(schema_info)
                    }

        except Exception as e:
            logger.error(f"获取表结构失败: {e}")
            return {
                "success": False,
                "error": f"获取表结构失败: {str(e)}"
            }

    async def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        获取表的样本数据
        """
        # 验证表名安全性
        if not table_name.replace('_', '').replace('-', '').isalnum():
            return {"success": False, "error": "非法的表名"}

        sql = f"SELECT * FROM `{table_name}` LIMIT {limit}"
        return await self.execute_query(sql)


# 全局服务实例
mysql_service = MySQLService()
