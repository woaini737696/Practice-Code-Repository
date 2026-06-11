import httpx
import json
from typing import List, Dict, Any, Optional
from app.config import settings


class ModelGateway:
    """统一模型网关，支持所有OpenAI兼容API"""
    
    @staticmethod
    async def chat_completion(
        base_url: str,
        api_key: str,
        model_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 30,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用模型API进行对话"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 如果有system_prompt，插入到messages开头
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def build_distillation_prompt(chat_records: List[Dict[str, Any]], target_message: str) -> List[Dict[str, str]]:
        """构建蒸馏prompt，让模型学习用户风格"""
        
        # 取最近10条记录作为示例
        recent_records = chat_records[-10:] if len(chat_records) > 10 else chat_records
        
        examples = []
        for record in recent_records:
            role = record.get("role", "user")
            content = record.get("content", "")
            examples.append(f"{'对方' if role == 'user' else '我'}: {content}")
        
        system_content = f"""你正在模拟一个真实用户进行社交聊天。请参考以下该用户的历史聊天风格，用相似的语气、用词习惯和思维方式进行回复。

历史聊天示例：
{chr(10).join(examples)}

要求：
1. 回复风格要与示例用户一致
2. 保持自然、口语化
3. 适当使用表情符号和网络用语
4. 回复长度与示例相似
5. 要像真实的人类朋友一样聊天，不要像AI助手"""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": target_message}
        ]
        
        return messages
    
    @staticmethod
    def build_scoring_prompt(conversation: List[Dict[str, Any]], dimensions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """构建评分prompt"""
        
        dimension_descriptions = []
        for dim in dimensions:
            dimension_descriptions.append(
                f"- {dim['name']}（权重{dim['weight']}）: {dim.get('description', '')}"
            )
        
        conversation_text = []
        for msg in conversation:
            role = "用户" if msg.get("role") == "user" else "AI"
            conversation_text.append(f"{role}: {msg.get('content', '')}")
        
        system_content = f"""你是一个专业的AI对话质量评估专家。请对以下AI对话进行多维度评分。

评分维度：
{chr(10).join(dimension_descriptions)}

请按以下JSON格式输出评分结果（不要输出其他内容）：
{{
  "scores": {{
    "维度名称": {{"score": 分数(1-10), "reason": "评分理由"}},
    ...
  }},
  "total_score": 总分(1-100),
  "summary": "总体评价（50字以内）"
}}"""

        user_content = f"请评分以下对话：\n\n{chr(10).join(conversation_text)}"
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        
        return messages
