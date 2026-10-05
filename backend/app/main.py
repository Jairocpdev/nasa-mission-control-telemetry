from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/mission_control")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = set()

@app.get("/telemetry/history")
async def history(limit: int = 100):
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT :limit"), {"limit": limit})
        rows = result.mappings().all()
        return [dict(r) for r in rows]

@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(ws)

@app.get("/")
async def root():
    return {"status": "【entity-NASA¦canonical_name=NASA】 MISSION CONTROL ONLINE", "pipeline": "satellite.py -> Redis -> ingestor.py -> TimescaleDB -> FastAPI"}