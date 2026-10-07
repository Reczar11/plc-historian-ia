import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..db import get_connection
from ..auth import require_role

router = APIRouter()

VALID_DATA_SOURCES = ('simulated', 'real', 'modbus')


class PLCConfigIn(BaseModel):
    plc_ip: Optional[str] = None
    data_source: str = 'simulated'
    port: Optional[int] = None
    unit_id: Optional[int] = None


@router.get('/plc/config')
def get_plc_config(dep=Depends(require_role('operator', 'engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT plc_ip, data_source, port, unit_id, updated_at FROM plc_config WHERE id = 1')
            row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail='PLC config not found')
        return row
    finally:
        conn.close()


@router.put('/plc/config')
def update_plc_config(config: PLCConfigIn, dep=Depends(require_role('engineer', 'admin'))):
    if config.data_source not in VALID_DATA_SOURCES:
        raise HTTPException(status_code=422, detail="data_source must be one of: " + ", ".join(VALID_DATA_SOURCES))
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE plc_config SET plc_ip = %s, data_source = %s, port = %s, unit_id = %s, updated_at = now() WHERE id = 1',
                (config.plc_ip, config.data_source, config.port, config.unit_id),
            )
            updated = cur.rowcount
        conn.commit()
        if updated == 0:
            raise HTTPException(status_code=404, detail='PLC config not found')
        return {'updated': True}
    finally:
        conn.close()
