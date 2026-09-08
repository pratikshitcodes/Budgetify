from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import io
import datetime

from ..database import get_db
from .. import oauth, schemas
from ..services import analytics_service, report_service

router = APIRouter(
    prefix='/reports',
    tags=['Reports']
)

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[schemas.Token, Depends(oauth.get_current_user)]

@router.get('/monthly/{year}/{month}')
def get_monthly_report(year: int, month: int, db: DbSession, current_user: CurrentUser):
    data = analytics_service.get_detailed_analysis(db, current_user.id, month, year)
    return {"type": "monthly", "data": data, "pdf_url": f"/reports/monthly/{year}/{month}/pdf", "csv_url": f"/reports/monthly/{year}/{month}/csv"}

@router.get('/monthly/{year}/{month}/pdf')
def get_monthly_pdf(year: int, month: int, db: DbSession, current_user: CurrentUser):
    data = analytics_service.get_detailed_analysis(db, current_user.id, month, year)
    pdf_bytes = report_service.generate_pdf(data, is_comparison=False)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=budgetify_report_{year}_{month}.pdf"}
    )

@router.get('/monthly/{year}/{month}/csv')
def get_monthly_csv(year: int, month: int, db: DbSession, current_user: CurrentUser):
    data = analytics_service.get_detailed_analysis(db, current_user.id, month, year)
    csv_str = report_service.generate_csv(data, is_comparison=False)
    return StreamingResponse(
        io.StringIO(csv_str),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=budgetify_report_{year}_{month}.csv"}
    )

@router.get('/compare')
def get_compare_report(month1: int, year1: int, month2: int, year2: int, db: DbSession, current_user: CurrentUser):
    data = analytics_service.compare_months(db, current_user.id, month1, year1, month2, year2)
    return {
        "type": "comparison", 
        "data": data, 
        "pdf_url": f"/reports/compare/pdf?month1={month1}&year1={year1}&month2={month2}&year2={year2}", 
        "csv_url": f"/reports/compare/csv?month1={month1}&year1={year1}&month2={month2}&year2={year2}"
    }

@router.get('/compare/pdf')
def get_compare_pdf(month1: int, year1: int, month2: int, year2: int, db: DbSession, current_user: CurrentUser):
    data = analytics_service.compare_months(db, current_user.id, month1, year1, month2, year2)
    pdf_bytes = report_service.generate_pdf(data, is_comparison=True)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=budgetify_comparison.pdf"}
    )

@router.get('/compare/csv')
def get_compare_csv(month1: int, year1: int, month2: int, year2: int, db: DbSession, current_user: CurrentUser):
    data = analytics_service.compare_months(db, current_user.id, month1, year1, month2, year2)
    csv_str = report_service.generate_csv(data, is_comparison=True)
    return StreamingResponse(
        io.StringIO(csv_str),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=budgetify_comparison.csv"}
    )

@router.get('/battle', response_model=schemas.MonthBattleResponse)
def get_month_battle(month1: int, year1: int, month2: int, year2: int, db: DbSession, current_user: CurrentUser):
    return analytics_service.month_battle(db, current_user.id, month1, year1, month2, year2)
