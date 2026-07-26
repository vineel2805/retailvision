"""Reports and export REST API router (FR-009, FR-010)."""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, Response
from fastapi.responses import Response

from backend.api.deps import engine
from backend.utils.exporter import ReportExporter

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/summary")
def get_report_summary(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    """Return hourly breakdown and peak hours for date range."""
    s_date = date.fromisoformat(start_date) if start_date else date.today()
    e_date = date.fromisoformat(end_date) if end_date else date.today()

    return engine.repository.get_period_summary(s_date, e_date)


@router.get("/export/{format}")
def export_report(
    format: str,
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    """Export footfall report in CSV, XLSX, or PDF format."""
    s_date = date.fromisoformat(start_date) if start_date else date.today()
    e_date = date.fromisoformat(end_date) if end_date else date.today()

    data = engine.repository.get_period_summary(s_date, e_date)
    filename = f"retailvision_report_{s_date.isoformat()}_{e_date.isoformat()}"

    fmt = format.lower()
    if fmt == "csv":
        content = ReportExporter.to_csv(data)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )
    elif fmt in ("xlsx", "excel"):
        content_bytes = ReportExporter.to_xlsx(data)
        return Response(
            content=content_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )
    elif fmt == "pdf":
        content_bytes = ReportExporter.to_pdf(data)
        return Response(
            content=content_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
        )
    else:
        return Response(status_code=400, content="Invalid format. Use csv, xlsx, or pdf.")
