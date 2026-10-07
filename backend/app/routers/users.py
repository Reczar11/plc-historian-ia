import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..db import get_connection
from ..auth import require_role, hash_password

router = APIRouter()

VALID_ROLES = ('operator', 'engineer', 'admin')


class UserIn(BaseModel):
    username: str
    password: str
    role: str


class UserUpdateIn(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None


@router.get('/users')
def list_users(dep=Depends(require_role('admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, username, role, created_at FROM users ORDER BY username')
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()


@router.post('/users')
def create_user(user: UserIn, dep=Depends(require_role('admin'))):
    if user.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail="role must be one of: " + ", ".join(VALID_ROLES))
    if not user.password or len(user.password) < 6:
        raise HTTPException(status_code=422, detail='Password must be at least 6 characters')

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    'INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id',
                    (user.username, hash_password(user.password), user.role),
                )
                new_id = cur.fetchone()['id']
            except psycopg2.IntegrityError:
                conn.rollback()
                raise HTTPException(status_code=409, detail='A user with this username already exists')
        conn.commit()
        return {'id': new_id}
    finally:
        conn.close()


@router.put('/users/{user_id}')
def update_user(user_id: int, user: UserUpdateIn, dep=Depends(require_role('admin'))):
    if user.role is not None and user.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail="role must be one of: " + ", ".join(VALID_ROLES))
    if user.password is not None and len(user.password) < 6:
        raise HTTPException(status_code=422, detail='Password must be at least 6 characters')
    if user.role is None and user.password is None:
        raise HTTPException(status_code=422, detail='Provide role and/or password to update')

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if user.password is not None and user.role is not None:
                cur.execute(
                    'UPDATE users SET password_hash = %s, role = %s WHERE id = %s',
                    (hash_password(user.password), user.role, user_id),
                )
            elif user.password is not None:
                cur.execute(
                    'UPDATE users SET password_hash = %s WHERE id = %s',
                    (hash_password(user.password), user_id),
                )
            else:
                cur.execute(
                    'UPDATE users SET role = %s WHERE id = %s',
                    (user.role, user_id),
                )
            updated = cur.rowcount
        conn.commit()
        if updated == 0:
            raise HTTPException(status_code=404, detail='User not found')
        return {'updated': True}
    finally:
        conn.close()


@router.delete('/users/{user_id}')
def delete_user(user_id: int, current_user=Depends(require_role('admin'))):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT username FROM users WHERE id = %s', (user_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail='User not found')
            if row['username'] == current_user['username']:
                raise HTTPException(status_code=400, detail='You cannot delete your own account')

            cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
            deleted = cur.rowcount
        conn.commit()
        if deleted == 0:
            raise HTTPException(status_code=404, detail='User not found')
        return {'deleted': True}
    finally:
        conn.close()
