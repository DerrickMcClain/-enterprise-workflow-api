import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.redis_client import get_redis
from app.database import get_db

log = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/health", response_model=dict[str, Any])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": get_settings().app_name,
    }


@router.get("/ready", response_model=dict[str, Any])
def ready(db: Session = Depends(get_db)) -> dict[str, Any]:
    ok_db = True
    ok_cache = True
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001
        log.warning("readiness db failed: %s", e)
        ok_db = False
    try:
        get_redis().ping()
    except Exception as e:  # noqa: BLE001
        log.warning("readiness redis failed: %s", e)
        ok_cache = False
    return {"database": ok_db, "redis": ok_cache, "ready": ok_db and ok_cache}
