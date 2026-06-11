from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.test import Test
from app.models.test_result import TestResult
from app.models.ai_model import AIModel
from app.models.distilled_user import DistilledUser
from app.models.score_dimension import ScoreDimension
from app.schemas.test import TestCreate, TestResponse, TestDetail
from app.core.report_generator import ReportGenerator
from app.tasks.test_tasks import run_test_task

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.get("", response_model=List[TestResponse])
def list_tests(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取测试列表"""
    query = db.query(Test)
    if status:
        query = query.filter(Test.status == status)
    tests = query.order_by(Test.created_at.desc()).offset(skip).limit(limit).all()
    return tests


@router.post("", response_model=TestResponse)
def create_test(test: TestCreate, db: Session = Depends(get_db)):
    """创建测试任务"""
    db_test = Test(
        name=test.name,
        user_ids=test.user_ids,
        model_ids=test.model_ids,
        config=test.config,
        status="pending"
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test


@router.post("/{test_id}/start")
def start_test(test_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """启动测试任务"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    if test.status not in ["pending", "failed"]:
        raise HTTPException(status_code=400, detail="测试状态不允许启动")
    
    # 使用Celery异步执行测试
    run_test_task.delay(test_id)
    
    test.status = "running"
    test.progress = 0
    db.commit()
    
    return {"message": "测试已启动", "test_id": test_id}


@router.get("/{test_id}", response_model=TestDetail)
def get_test(test_id: int, db: Session = Depends(get_db)):
    """获取测试详情"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    # 获取测试结果
    results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    
    # 构建详细结果
    detailed_results = []
    for result in results:
        model = db.query(AIModel).filter(AIModel.id == result.model_id).first()
        user = db.query(DistilledUser).filter(DistilledUser.id == result.user_id).first()
        
        detailed_results.append({
            "id": result.id,
            "model_id": result.model_id,
            "model_name": model.name if model else "未知",
            "user_id": result.user_id,
            "user_name": user.name if user else "未知",
            "conversation": result.conversation,
            "scores": result.scores,
            "total_score": float(result.total_score) if result.total_score else None,
            "created_at": result.created_at.isoformat() if result.created_at else None
        })
    
    test.results = detailed_results
    return test


@router.post("/{test_id}/cancel")
def cancel_test(test_id: int, db: Session = Depends(get_db)):
    """取消测试"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    if test.status != "running":
        raise HTTPException(status_code=400, detail="只有运行中的测试可以取消")
    
    test.status = "cancelled"
    db.commit()
    return {"message": "测试已取消"}


@router.delete("/{test_id}")
def delete_test(test_id: int, db: Session = Depends(get_db)):
    """删除测试"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    # 删除关联的测试结果
    db.query(TestResult).filter(TestResult.test_id == test_id).delete()
    db.delete(test)
    db.commit()
    return {"message": "删除成功"}


@router.get("/{test_id}/report")
def generate_report(test_id: int, format: str = "pdf", db: Session = Depends(get_db)):
    """生成测试报告"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    # 构建报告数据
    results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    dimensions = db.query(ScoreDimension).filter(ScoreDimension.is_enabled == 1).all()
    
    # 获取模型和用户名称
    model_ids = set()
    user_ids = set()
    detailed_results = []
    model_scores = {}
    
    for result in results:
        model = db.query(AIModel).filter(AIModel.id == result.model_id).first()
        user = db.query(DistilledUser).filter(DistilledUser.id == result.user_id).first()
        
        model_ids.add(result.model_id)
        user_ids.add(result.user_id)
        
        detailed_results.append({
            "model_name": model.name if model else "未知",
            "user_name": user.name if user else "未知",
            "total_score": float(result.total_score) if result.total_score else 0,
            "scores": result.scores or {}
        })
        
        # 计算模型平均分
        model_name = model.name if model else "未知"
        if model_name not in model_scores:
            model_scores[model_name] = []
        if result.total_score:
            model_scores[model_name].append(float(result.total_score))
    
    # 计算排名
    model_ranking = []
    for model_name, scores in model_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        model_ranking.append({"name": model_name, "avg_score": avg_score})
    model_ranking.sort(key=lambda x: x["avg_score"], reverse=True)
    
    test_data = {
        "name": test.name,
        "status": test.status,
        "created_at": test.created_at.isoformat() if test.created_at else "",
        "completed_at": test.completed_at.isoformat() if test.completed_at else "",
        "models": list(model_ids),
        "users": list(user_ids),
        "dimensions": [{"name": d.name, "weight": float(d.weight)} for d in dimensions],
        "results": detailed_results,
        "model_ranking": model_ranking
    }
    
    # 生成报告
    if format == "pdf":
        pdf_bytes = ReportGenerator.generate_pdf(test_data)
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=test_report_{test_id}.pdf"}
        )
    elif format == "excel":
        excel_bytes = ReportGenerator.generate_excel(test_data)
        from fastapi.responses import Response
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=test_report_{test_id}.xlsx"}
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的格式，只支持pdf或excel")
