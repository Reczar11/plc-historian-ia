import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..db import get_connection
from ..auth import decode_token

router = APIRouter()

MIN_INTERVAL = 0.5
DEFAULT_TAGS = ['Temperature', 'Pressure', 'Vibration', 'MotorCurrent']
ALLOWED_ROLES = ('operator', 'engineer', 'admin')


@router.websocket('/ws/live')
async def websocket_live(websocket: WebSocket):
    params = websocket.query_params
    token = params.get('token')
    payload = decode_token(token) if token else None
    if payload is None or payload.get('role') not in ALLOWED_ROLES:
        await websocket.close(code=4401)
        return

    tags_param = params.get('tags')
    if tags_param:
        tags = [t.strip() for t in tags_param.split(',') if t.strip()]
    else:
        tags = DEFAULT_TAGS

    try:
        interval = float(params.get('interval', '1'))
    except ValueError:
        interval = 1.0
    if interval < MIN_INTERVAL:
        interval = MIN_INTERVAL

    await websocket.accept()
    try:
        while True:
            conn = get_connection()
            with conn.cursor() as cur:
                placeholders = ','.join(['%s'] * len(tags))
                query = 'SELECT DISTINCT ON (tag_name) time, tag_name, value, quality FROM plc_readings WHERE tag_name IN (' + placeholders + ') ORDER BY tag_name, time DESC'
                cur.execute(query, tuple(tags))
                rows = cur.fetchall()
            conn.close()
            payload_out = []
            for row in rows:
                payload_out.append({
                    'time': row['time'].isoformat(),
                    'tag_name': row['tag_name'],
                    'value': row['value'],
                    'quality': row['quality'],
                })
            await websocket.send_json(payload_out)
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass
