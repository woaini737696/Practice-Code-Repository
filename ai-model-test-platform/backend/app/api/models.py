from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.ai_model import AIModel
from app.schemas.ai_model import AIModelCreate, AIModelResponse

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[AIModelResponse])
def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取AI模型列表"""
    models = db.query(AIModel).offset(skip).limit(limit).all()
    return models


@router.post("", response_model=AIModelResponse)
def create_model(model: AIModelCreate, db: Session = Depends(get_db)):
    """创建AI模型配置"""
    db_model = AIModel(**model.dict())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


@router.get("/{model_id}", response_model=AIModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    """获取模型详情"""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.put("/{model_id}", response_model=AIModelResponse)
def update_model(model_id: int, model_update: AIModelCreate, db: Session = Depends(get_db)):
    """更新模型配置"""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    for key, value in model_update.dict().items():
        setattr(model, key, value)
    
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    """删除模型"""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    db.delete(model)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{model_id}/toggle")
def toggle_model(model_id: int, db: Session = Depends(get_db)):
    """启用/禁用模型"""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    model.is_enabled = 0 if model.is_enabled == 1 else 1
    db.commit()
    return {"message": "状态更新成功", "is_enabled": model.is_enabled}
