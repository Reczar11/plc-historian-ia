from fastapi import FastAPI
from .routers import readings, live, tags, auth_router, assets, alarms, plc_config, users, reports

app = FastAPI(title='PLC Historian API')

app.include_router(auth_router.router)
app.include_router(readings.router)
app.include_router(live.router)
app.include_router(tags.router)
app.include_router(assets.router)
app.include_router(alarms.router)
app.include_router(plc_config.router)
app.include_router(users.router)
app.include_router(reports.router)


@app.get('/health')
def health():
    return {'status': 'ok'}
