from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from ..db import get_connection
from ..auth import verify_api_key

router = APIRouter()

TABLES = {
    'raw': 'plc_readings',
    '1min': 'plc_readings_1min',
    '1hour': 'plc_readings_1hour',
}

MAX_ROWS = 10000
RAW_MAX_RANGE_SECONDS = 24 * 60 * 60


@router.get('/readings')
def get_readings(tag_name: str, start: str, end: str, resolution: str = 'raw', limit: int = 5000, dep=Depends(verify_api_key)):
    if resolution not in TABLES:
        raise HTTPException(status_code=400, detail='resolution must be one of: raw, 1min, 1hour')
    if limit > MAX_ROWS:
        limit = MAX_ROWS

    if resolution == 'raw':
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            range_seconds = (end_dt - start_dt).total_seconds()
        except ValueError:
            range_seconds = 0
        if range_seconds > RAW_MAX_RANGE_SECONDS:
            raise HTTPException(
                status_code=400,
                detail='Range too large for raw resolution (max 24 hours). Use resolution=1min or 1hour for longer ranges.',
            )

    table = TABLES[resolution]
    time_column = 'time' if resolution == 'raw' else 'bucket'
    value_column = 'value' if resolution == 'raw' else 'avg_value'
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = 'SELECT ' + time_column + ' AS time, ' + value_column + ' AS value FROM ' + table + ' WHERE tag_name = %s AND ' + time_column + ' BETWEEN %s AND %s ORDER BY ' + time_column + ' LIMIT %s'
            cur.execute(query, (tag_name, start, end, limit))
            rows = cur.fetchall()
        result = []
        for row in rows:
            result.append({'time': row['time'].isoformat(), 'value': row['value']})
        return result
    finally:
        conn.close()
