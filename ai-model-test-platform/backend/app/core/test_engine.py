import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.test import Test
from app.models.test_result import TestResult
from app.models.distilled_user import DistilledUser
from app.models.chat_record import ChatRecord
from app.models.ai_model import AIModel
from app.models.score_dimension import ScoreDimension
from app.core.model_gateway import ModelGateway


class TestEngine:
    """测试引擎，执行批量测试"""
    
    def __init__(self):
        self.model_gateway = ModelGateway()
    
    async def run_test(self, test_id: int, progress_callback=None):
        """运行测试任务"""
        db = SessionLocal()
        try:
            test = db.query(Test).filter(Test.id == test_id).first()
            if not test:
                return
            
            # 更新状态为进行中
            test.status = "running"
            db.commit()
            
            # 获取测试用户
            users = db.query(DistilledUser).filter(
                DistilledUser.id.in_(test.user_ids),
                DistilledUser.status == 1
            ).all()
            
            # 获取测试模型
            models = db.query(AIModel).filter(
                AIModel.id.in_(test.model_ids),
                AIModel.is_enabled == 1
            ).all()
            
            # 获取评分维度
            dimensions = db.query(ScoreDimension).filter(
                ScoreDimension.is_enabled == 1
            ).order_by(ScoreDimension.sort_order).all()
            
            total_tasks = len(users) * len(models)
            completed_tasks = 0
            
            for user in users:
                # 获取用户聊天记录
                chat_records = db.query(ChatRecord).filter(
                    ChatRecord.user_id == user.id
                ).order_by(ChatRecord.timestamp).all()
                
                records_data = [
                    {"role": r.role, "content": r.content, "timestamp": str(r.timestamp)}
                    for r in chat_records
                ]
                
                for model in models:
                    try:
                        # 执行对话测试
                        conversation = await self._run_conversation_test(
                            model, user, records_data
                        )
                        
                        # AI评分
                        scores = await self._score_conversation(
                            model, conversation, dimensions
                        )
                        
                        # 保存结果
                        result = TestResult(
                            test_id=test_id,
                            model_id=model.id,
                            user_id=user.id,
                            conversation=conversation,
                            scores=scores.get("scores"),
                            total_score=scores.get("total_score")
                        )
                        db.add(result)
                        db.commit()
                        
                    except Exception as e:
                        print(f"Test failed for user {user.id}, model {model.id}: {str(e)}")
                        # 保存失败结果
                        result = TestResult(
                            test_id=test_id,
                            model_id=model.id,
                            user_id=user.id,
                            conversation=[{"error": str(e)}],
                            scores=None,
                            total_score=None
                        )
                        db.add(result)
                        db.commit()
                    
                    completed_tasks += 1
                    progress = int((completed_tasks / total_tasks) * 100)
                    test.progress = progress
                    db.commit()
                    
                    # 推送进度
                    if progress_callback:
                        await progress_callback(test_id, progress, test.status)
            
            # 更新状态为已完成
            test.status = "completed"
            test.progress = 100
            from datetime import datetime
            test.completed_at = datetime.now()
            db.commit()
            
            if progress_callback:
                await progress_callback(test_id, 100, "completed")
                
        except Exception as e:
            test.status = "failed"
            db.commit()
            if progress_callback:
                await progress_callback(test_id, test.progress, "failed")
            raise e
        finally:
            db.close()
    
    async def _run_conversation_test(
        self, 
        model: AIModel, 
        user: DistilledUser, 
        chat_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """执行一轮对话测试"""
        
        # 构建测试对话（模拟3轮对话）
        conversation = []
        
        # 准备测试消息（可以从聊天记录中提取对方的消息作为输入）
        test_messages = [
            "最近怎么样？",
            "哈哈真的吗，我也觉得",
            "周末有什么安排呀"
        ]
        
        for test_msg in test_messages:
            # 用户消息
            conversation.append({"role": "user", "content": test_msg})
            
            # 构建蒸馏prompt
            messages = self.model_gateway.build_distillation_prompt(
                chat_records, test_msg
            )
            
            # 调用模型
            response = await self.model_gateway.chat_completion(
                base_url=model.base_url,
                api_key=model.api_key,
                model_name=model.model_name,
                messages=messages,
                temperature=float(model.temperature),
                max_tokens=model.max_tokens,
                timeout=model.timeout
            )
            
            ai_reply = response["choices"][0]["message"]["content"]
            conversation.append({"role": "assistant", "content": ai_reply})
        
        return conversation
    
    async def _score_conversation(
        self,
        model: AIModel,
        conversation: List[Dict[str, Any]],
        dimensions: List[ScoreDimension]
    ) -> Dict[str, Any]:
        """对对话进行评分"""
        
        dimensions_data = [
            {
                "name": d.name,
                "weight": float(d.weight),
                "description": d.description or ""
            }
            for d in dimensions
        ]
        
        messages = self.model_gateway.build_scoring_prompt(
            conversation, dimensions_data
        )
        
        # 使用第一个启用的模型作为评分模型，或者使用默认模型
        # 这里简化处理，使用被测模型自己评分（实际应该用独立评分模型）
        response = await self.model_gateway.chat_completion(
            base_url=model.base_url,
            api_key=model.api_key,
            model_name=model.model_name,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            timeout=60
        )
        
        content = response["choices"][0]["message"]["content"]
        
        # 解析JSON
        try:
            # 尝试直接解析
            scores = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从markdown代码块中提取
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                scores = json.loads(json_match.group(1))
            else:
                # 尝试提取花括号内容
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    scores = json.loads(json_match.group(0))
                else:
                    scores = {"scores": {}, "total_score": 0, "summary": "解析失败"}
        
        return scores
