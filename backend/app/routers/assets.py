from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..db import get_connection
from ..auth import require_role

router = APIRouter()

VALID_TYPES = ('plant', 'area', 'line', 'equipment')


class AssetIn(BaseModel):
    name: str
    asset_type: str
    parent_id: Optional[int] = None


@router.get('/assets')
def list_assets(dep=Depends(require_role('operator', 'engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, asset_type, parent_id FROM assets ORDER BY id')
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def build_tree(assets, tags_by_asset, parent_id=None):
    nodes = []
    for asset in assets:
        if asset['parent_id'] == parent_id:
            node = dict(asset)
            node['children'] = build_tree(assets, tags_by_asset, asset['id'])
            node['tags'] = tags_by_asset.get(asset['id'], [])
            nodes.append(node)
    return nodes


@router.get('/assets/tree')
def get_asset_tree(dep=Depends(require_role('operator', 'engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, asset_type, parent_id FROM assets ORDER BY id')
            assets = cur.fetchall()
            cur.execute('SELECT id, name, asset_id FROM tags WHERE asset_id IS NOT NULL')
            tag_rows = cur.fetchall()
        tags_by_asset = {}
        for row in tag_rows:
            tags_by_asset.setdefault(row['asset_id'], []).append({'id': row['id'], 'name': row['name']})
        return build_tree(assets, tags_by_asset, None)
    finally:
        conn.close()


@router.post('/assets')
def create_asset(asset: AssetIn, dep=Depends(require_role('engineer', 'admin'))):
    if asset.asset_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail='asset_type must be one of: plant, area, line, equipment')
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO assets (name, asset_type, parent_id) VALUES (%s, %s, %s) RETURNING id',
                (asset.name, asset.asset_type, asset.parent_id),
            )
            new_id = cur.fetchone()['id']
        conn.commit()
        return {'id': new_id}
    finally:
        conn.close()


@router.put('/assets/{asset_id}')
def update_asset(asset_id: int, asset: AssetIn, dep=Depends(require_role('engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE assets SET name = %s, asset_type = %s, parent_id = %s WHERE id = %s',
                (asset.name, asset.asset_type, asset.parent_id, asset_id),
            )
            updated = cur.rowcount
        conn.commit()
        if updated == 0:
            raise HTTPException(status_code=404, detail='Asset not found')
        return {'updated': True}
    finally:
        conn.close()


@router.delete('/assets/{asset_id}')
def delete_asset(asset_id: int, dep=Depends(require_role('engineer', 'admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM assets WHERE id = %s', (asset_id,))
            deleted = cur.rowcount
        conn.commit()
        if deleted == 0:
            raise HTTPException(status_code=404, detail='Asset not found')
        return {'deleted': True}
    finally:
        conn.close()
