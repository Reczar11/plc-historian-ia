from fastapi import FastAPI
from .routers import readings, live

app = FastAPI(title='PLC Historian API')

app.include_router(readings.router)
app.include_router(live.router)


@app.get('/health')
def health():
    return {'status': 'ok'}
