from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.system_config import SystemConfig
from app.schemas.system_config import SystemConfigCreate, SystemConfigResponse
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=List[SystemConfigResponse])
def list_settings(db: Session = Depends(get_db)):
    """获取所有系统配置"""
    configs = db.query(SystemConfig).all()
    return configs


@router.get("/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    """获取指定配置"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.post("", response_model=SystemConfigResponse)
def create_or_update_setting(config: SystemConfigCreate, db: Session = Depends(get_db)):
    """创建或更新配置"""
    existing = db.query(SystemConfig).filter(SystemConfig.config_key == config.config_key).first()
    
    if existing:
        existing.config_value = config.config_value
        existing.description = config.description
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_config = SystemConfig(**config.dict())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config


@router.delete("/{key}")
def delete_setting(key: str, db: Session = Depends(get_db)):
    """删除配置"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.delete(config)
    db.commit()
    return {"message": "删除成功"}


@router.get("/email/config")
def get_email_config():
    """获取邮箱配置（脱敏）"""
    return {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user,
        "smtp_tls": settings.smtp_tls,
        "configured": bool(settings.smtp_user and settings.smtp_password)
    }


@router.post("/email/test")
def test_email_config(to_email: str):
    """测试邮件配置"""
    import asyncio
    from app.services.email_service import EmailService
    
    try:
        asyncio.run(EmailService.send_test_completion_email(
            to_email=to_email,
            test_name="测试邮件",
            test_id=0,
            status="completed"
        ))
        return {"message": "测试邮件已发送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")
