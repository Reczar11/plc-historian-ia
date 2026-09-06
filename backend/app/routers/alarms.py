from fastapi import APIRouter, Depends, HTTPException
from ..db import get_connection
from ..auth import require_role

router = APIRouter()


@router.get('/alarms')
def list_alarms(status: str = 'active', dep=Depends(require_role('operator', 'engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if status == 'all':
                cur.execute('SELECT * FROM alarm_events ORDER BY triggered_at DESC LIMIT 200')
            else:
                cur.execute('SELECT * FROM alarm_events WHERE status = %s ORDER BY triggered_at DESC LIMIT 200', (status,))
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()


@router.post('/alarms/{alarm_id}/acknowledge')
def acknowledge_alarm(alarm_id: int, current_user: dict = Depends(require_role('operator', 'engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE alarm_events SET acknowledged = true, acknowledged_by = %s, acknowledged_at = now() WHERE id = %s',
                (current_user['username'], alarm_id),
            )
            updated = cur.rowcount
        conn.commit()
        if updated == 0:
            raise HTTPException(status_code=404, detail='Alarm not found')
        return {'acknowledged': True}
    finally:
        conn.close()
