from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.score_dimension import ScoreDimension
from app.models.annotation import Annotation
from app.models.test_result import TestResult
from app.schemas.score_dimension import ScoreDimensionCreate, ScoreDimensionResponse
from app.schemas.annotation import AnnotationCreate, AnnotationResponse

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


# 评分维度管理
@router.get("/dimensions", response_model=List[ScoreDimensionResponse])
def list_dimensions(db: Session = Depends(get_db)):
    """获取评分维度列表"""
    dimensions = db.query(ScoreDimension).filter(
        ScoreDimension.is_enabled == 1
    ).order_by(ScoreDimension.sort_order).all()
    return dimensions


@router.post("/dimensions", response_model=ScoreDimensionResponse)
def create_dimension(dimension: ScoreDimensionCreate, db: Session = Depends(get_db)):
    """创建评分维度"""
    db_dimension = ScoreDimension(**dimension.dict())
    db.add(db_dimension)
    db.commit()
    db.refresh(db_dimension)
    return db_dimension


@router.put("/dimensions/{dimension_id}", response_model=ScoreDimensionResponse)
def update_dimension(
    dimension_id: int,
    dimension_update: ScoreDimensionCreate,
    db: Session = Depends(get_db)
):
    """更新评分维度"""
    dimension = db.query(ScoreDimension).filter(ScoreDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="维度不存在")
    
    for key, value in dimension_update.dict().items():
        setattr(dimension, key, value)
    
    db.commit()
    db.refresh(dimension)
    return dimension


@router.delete("/dimensions/{dimension_id}")
def delete_dimension(dimension_id: int, db: Session = Depends(get_db)):
    """删除评分维度（软删除）"""
    dimension = db.query(ScoreDimension).filter(ScoreDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="维度不存在")
    
    dimension.is_enabled = 0
    db.commit()
    return {"message": "删除成功"}


# 数据标注
@router.get("/annotations", response_model=List[AnnotationResponse])
def list_annotations(result_id: int = None, db: Session = Depends(get_db)):
    """获取标注列表"""
    query = db.query(Annotation)
    if result_id:
        query = query.filter(Annotation.result_id == result_id)
    annotations = query.all()
    return annotations


@router.post("/annotations", response_model=AnnotationResponse)
def create_annotation(annotation: AnnotationCreate, db: Session = Depends(get_db)):
    """创建标注"""
    # 检查测试结果是否存在
    result = db.query(TestResult).filter(TestResult.id == annotation.result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="测试结果不存在")
    
    db_annotation = Annotation(**annotation.dict())
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    return db_annotation


@router.put("/annotations/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(
    annotation_id: int,
    annotation_update: AnnotationCreate,
    db: Session = Depends(get_db)
):
    """更新标注"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")
    
    for key, value in annotation_update.dict().items():
        setattr(annotation, key, value)
    
    db.commit()
    db.refresh(annotation)
    return annotation


@router.delete("/annotations/{annotation_id}")
def delete_annotation(annotation_id: int, db: Session = Depends(get_db)):
    """删除标注"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")
    
    db.delete(annotation)
    db.commit()
    return {"message": "删除成功"}
