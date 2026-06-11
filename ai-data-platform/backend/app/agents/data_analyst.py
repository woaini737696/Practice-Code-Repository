import json
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from app.core.config import settings
from app.services.mysql_service import mysql_service

logger = logging.getLogger(__name__)


class AgentState:
    """Agent状态"""
    def __init__(self):
        self.messages: List[Any] = []
        self.sql_query: Optional[str] = None
        self.query_result: Optional[Dict] = None
        self.analysis: Optional[str] = None
        self.suggestions: List[str] = []
        self.error: Optional[str] = None
        self.step: str = "start"


class DataAnalystAgent:
    """AI数据分析Agent"""

    def __init__(self):
        self.llm = None
        self.schema_info = None
        self.graph = None
        self._init_llm()

    def _init_llm(self):
        """延迟初始化LLM，避免启动时缺少API Key报错"""
        if not settings.LLM_API_KEY:
            return
        try:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=0.1,
                max_tokens=2000
            )
            self.graph = self._build_graph()
        except Exception as e:
            print(f"LLM初始化失败: {e}")

    async def _get_schema_context(self) -> str:
        """获取数据库schema上下文"""
        if self.schema_info is None:
            result = await mysql_service.get_schema()
            if result["success"]:
                self.schema_info = result["tables"]
            else:
                return "无法获取数据库结构"

        context = "数据库表结构:\n"
        for table in self.schema_info[:20]:  # 限制表数量
            context += f"\n表名: {table['table_name']}"
            if table['table_comment']:
                context += f" ({table['table_comment']})"
            context += "\n字段:\n"
            for col in table['columns']:
                comment = f" - {col['comment']}" if col['comment'] else ""
                context += f"  - {col['name']} ({col['type']}){comment}\n"
        return context

    def _build_graph(self) -> StateGraph:
        """构建Agent状态图"""
        workflow = StateGraph(AgentState)

        # 定义节点
        workflow.add_node("understand", self._understand_intent)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("analyze_result", self._analyze_result)
        workflow.add_node("handle_error", self._handle_error)

        # 定义边
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "generate_sql")
        workflow.add_edge("generate_sql", "execute_query")
        workflow.add_conditional_edges(
            "execute_query",
            self._should_analyze,
            {
                "analyze": "analyze_result",
                "error": "handle_error"
            }
        )
        workflow.add_edge("analyze_result", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    async def _understand_intent(self, state: AgentState) -> AgentState:
        """理解用户意图"""
        state.step = "understand"
        return state

    async def _generate_sql(self, state: AgentState) -> AgentState:
        """生成SQL查询"""
        state.step = "generate_sql"

        try:
            schema_context = await self._get_schema_context()
            user_message = state.messages[-1].content if state.messages else ""

            system_prompt = f"""你是一个专业的数据分析师，擅长将自然语言转换为MySQL SQL查询。

{schema_context}

规则:
1. 只生成SELECT查询，禁止任何修改数据的操作
2. 使用标准MySQL语法
3. 表名和字段名必须与上述schema一致
4. 时间筛选优先使用created_at字段
5. 聚合查询需要给字段起别名
6. 限制返回条数，默认最多100条

请直接返回SQL语句，不要有任何解释。"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]

            response = await self.llm.ainvoke(messages)
            sql = response.content.strip()

            # 清理SQL
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()

            state.sql_query = sql
            logger.info(f"生成的SQL: {sql}")

        except Exception as e:
            logger.error(f"生成SQL失败: {e}")
            state.error = f"生成SQL失败: {str(e)}"

        return state

    async def _execute_query(self, state: AgentState) -> AgentState:
        """执行SQL查询"""
        state.step = "execute_query"

        if state.error:
            return state

        if not state.sql_query:
            state.error = "没有生成SQL查询"
            return state

        result = await mysql_service.execute_query(state.sql_query)

        if result["success"]:
            state.query_result = result
        else:
            state.error = result.get("error", "查询执行失败")

        return state

    async def _analyze_result(self, state: AgentState) -> AgentState:
        """分析查询结果"""
        state.step = "analyze_result"

        if state.error:
            return state

        try:
            user_message = state.messages[-1].content if state.messages else ""
            result_data = state.query_result

            # 构建数据摘要
            data_summary = f"""
查询SQL: {result_data['sql']}
返回行数: {result_data['row_count']}
执行时间: {result_data['execution_time']}秒

数据样本(前5行):
{json.dumps(result_data['data'][:5], ensure_ascii=False, indent=2)}
"""

            system_prompt = """你是一个数据洞察专家。请根据查询结果给出简洁的业务洞察。

要求:
1. 用中文回答
2. 给出关键数字和趋势
3. 如果有异常，指出可能原因
4. 推荐下一步分析方向
5. 回答控制在200字以内"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"用户问题: {user_message}\n\n{data_summary}")
            ]

            response = await self.llm.ainvoke(messages)
            state.analysis = response.content.strip()

            # 生成建议
            state.suggestions = [
                "按时间趋势查看",
                "按渠道/维度拆分",
                "对比历史数据",
                "查看详细数据"
            ]

        except Exception as e:
            logger.error(f"分析结果失败: {e}")
            state.analysis = f"查询成功，返回{result_data['row_count']}条数据"

        return state

    async def _handle_error(self, state: AgentState) -> AgentState:
        """处理错误"""
        state.step = "handle_error"
        state.analysis = f"抱歉，分析过程中出现问题: {state.error}"
        return state

    def _should_analyze(self, state: AgentState) -> str:
        """判断下一步"""
        if state.error:
            return "error"
        return "analyze"

    async def chat(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        主对话接口

        Args:
            message: 用户消息
            history: 历史对话记录

        Returns:
            {
                "type": "data" | "text",
                "sql": str,
                "data": List[Dict],
                "columns": List[str],
                "analysis": str,
                "suggestions": List[str],
                "error": str
            }
        """
        if not self.llm or not self.graph:
            return {
                "type": "text",
                "analysis": "LLM尚未配置，请在.env文件中设置LLM_API_KEY。",
                "error": "LLM not configured"
            }

        state = AgentState()

        # 构建消息历史
        if history:
            for h in history:
                if h["role"] == "user":
                    state.messages.append(HumanMessage(content=h["content"]))
                else:
                    state.messages.append(AIMessage(content=h["content"]))

        state.messages.append(HumanMessage(content=message))

        try:
            # 运行Agent
            final_state = await self.graph.ainvoke(state)

            if final_state.error:
                return {
                    "type": "text",
                    "analysis": final_state.analysis or f"抱歉，分析失败: {final_state.error}",
                    "error": final_state.error
                }

            return {
                "type": "data",
                "sql": final_state.sql_query,
                "data": final_state.query_result.get("data", []),
                "columns": final_state.query_result.get("columns", []),
                "row_count": final_state.query_result.get("row_count", 0),
                "execution_time": final_state.query_result.get("execution_time", 0),
                "analysis": final_state.analysis or "",
                "suggestions": final_state.suggestions
            }

        except Exception as e:
            logger.error(f"Agent运行失败: {e}")
            return {
                "type": "text",
                "analysis": f"系统错误: {str(e)}",
                "error": str(e)
            }


# 全局Agent实例
agent = DataAnalystAgent()
