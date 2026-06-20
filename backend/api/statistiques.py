"""Route statistiques. GET /stats"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.services.stats_service import StatsService
from backend.core.dependencies import get_db, get_current_user
from typing import Optional

router = APIRouter()

@router.get("/")
def get_stats(periode: Optional[str] = Query(None), region: Optional[str] = Query(None),
              db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return StatsService(db).get_dashboard(periode, region)
