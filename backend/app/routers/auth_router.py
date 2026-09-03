from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db import get_connection
from ..auth import verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post('/auth/login')
def login(data: LoginRequest):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT username, password_hash, role FROM users WHERE username = %s', (data.username,))
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None or not verify_password(data.password, row['password_hash']):
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    token = create_access_token({'sub': row['username'], 'role': row['role']})
    return {'access_token': token, 'token_type': 'bearer', 'role': row['role']}
