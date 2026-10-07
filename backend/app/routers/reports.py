import io
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openpyxl import Workbook

from ..db import get_connection
from ..auth import require_role
from .readings import fetch_readings_rows, MAX_ROWS

router = APIRouter()

_INVALID_SHEET_CHARS = re.compile(r'[\\/*?:\[\]]')


class ExcelReportRequest(BaseModel):
    tags: list[str]
    start: str
    end: str
    resolution: str = '1min'


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = _INVALID_SHEET_CHARS.sub('_', name)[:31] or 'Sheet'
    candidate = cleaned
    suffix = 2
    while candidate in used:
        candidate = (cleaned[:28] + '_' + str(suffix))[:31]
        suffix += 1
    used.add(candidate)
    return candidate


@router.post('/reports/excel')
def export_excel_report(req: ExcelReportRequest, dep=Depends(require_role('operator', 'engineer', 'admin'))):
    if not req.tags:
        raise HTTPException(status_code=422, detail='Provide at least one tag')

    conn = get_connection()
    try:
        workbook = Workbook()
        workbook.remove(workbook.active)
        used_sheet_names: set = set()

        for tag_name in req.tags:
            rows = fetch_readings_rows(conn, tag_name, req.start, req.end, req.resolution, MAX_ROWS)
            sheet = workbook.create_sheet(title=_safe_sheet_name(tag_name, used_sheet_names))
            sheet.append(['Time', 'Value'])
            for row in rows:
                sheet.append([row['time'], row['value']])
            sheet.column_dimensions['A'].width = 28
            sheet.column_dimensions['B'].width = 14
    finally:
        conn.close()

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    filename = 'plc_report_' + timestamp + '.xlsx'
    return StreamingResponse(
        buffer,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="' + filename + '"'},
    )
