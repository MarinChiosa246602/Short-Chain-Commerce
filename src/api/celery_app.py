"""
Celery worker for background tasks.

Use for:
- Async batch processing
- Long-running extractions
- Scheduled tasks
"""

import os
from pathlib import Path

from celery import Celery

# Add src to path
SRC_ROOT = Path(__file__).resolve().parent
if str(SRC_ROOT.parent) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC_ROOT.parent))

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "shortchain_tasks",
    broker=redis_url,
    backend=redis_url,
    include=["src.api.celery_tasks"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=270,  # 4:30 minutes soft limit
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
)

if __name__ == "__main__":
    app.start()
