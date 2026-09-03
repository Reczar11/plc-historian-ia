from fastapi import FastAPI
from .routers import readings, live, tags, auth_router, assets

app = FastAPI(title='PLC Historian API')

app.include_router(auth_router.router)
app.include_router(readings.router)
app.include_router(live.router)
app.include_router(tags.router)
app.include_router(assets.router)


@app.get('/health')
def health():
    return {'status': 'ok'}
