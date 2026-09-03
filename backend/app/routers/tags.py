import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..db import get_connection
from ..auth import require_role

router = APIRouter()


class TagIn(BaseModel):
    name: str
    plc_address: Optional[str] = None
    data_type: str = 'REAL'
    engineering_unit: Optional[str] = None
    alarm_low: Optional[float] = None
    alarm_high: Optional[float] = None


@router.get('/tags')
def list_tags(dep=Depends(require_role('operator', 'engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, plc_address, data_type, engineering_unit, alarm_low, alarm_high FROM tags ORDER BY name')
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()


@router.post('/tags')
def create_tag(tag: TagIn, dep=Depends(require_role('engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    'INSERT INTO tags (name, plc_address, data_type, engineering_unit, alarm_low, alarm_high) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                    (tag.name, tag.plc_address, tag.data_type, tag.engineering_unit, tag.alarm_low, tag.alarm_high),
                )
            except psycopg2.IntegrityError:
                conn.rollback()
                raise HTTPException(status_code=409, detail='A tag with this name already exists')
            new_id = cur.fetchone()['id']
        conn.commit()
        return {'id': new_id}
    finally:
        conn.close()


@router.put('/tags/{tag_id}')
def update_tag(tag_id: int, tag: TagIn, dep=Depends(require_role('engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE tags SET name = %s, plc_address = %s, data_type = %s, engineering_unit = %s, alarm_low = %s, alarm_high = %s, updated_at = now() WHERE id = %s',
                (tag.name, tag.plc_address, tag.data_type, tag.engineering_unit, tag.alarm_low, tag.alarm_high, tag_id),
            )
            updated = cur.rowcount
        conn.commit()
        if updated == 0:
            raise HTTPException(status_code=404, detail='Tag not found')
        return {'updated': True}
    finally:
        conn.close()


@router.delete('/tags/{tag_id}')
def delete_tag(tag_id: int, dep=Depends(require_role('engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM tags WHERE id = %s', (tag_id,))
            deleted = cur.rowcount
        conn.commit()
        if deleted == 0:
            raise HTTPException(status_code=404, detail='Tag not found')
        return {'deleted': True}
    finally:
        conn.close()
