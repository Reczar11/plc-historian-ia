import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..db import get_connection
from ..auth import API_KEY

router = APIRouter()

MIN_INTERVAL = 0.5
DEFAULT_TAGS = ['Temperature', 'Pressure', 'Vibration', 'MotorCurrent']


@router.websocket('/ws/live')
async def websocket_live(websocket: WebSocket):
    params = websocket.query_params
    api_key = params.get('api_key')
    if api_key != API_KEY:
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
            payload = []
            for row in rows:
                payload.append({
                    'time': row['time'].isoformat(),
                    'tag_name': row['tag_name'],
                    'value': row['value'],
                    'quality': row['quality'],
                })
            await websocket.send_json(payload)
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass
