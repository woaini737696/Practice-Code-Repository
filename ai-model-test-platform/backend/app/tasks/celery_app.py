from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_test_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.test_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)
