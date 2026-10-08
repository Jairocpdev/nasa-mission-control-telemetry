from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/mission_control")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nasa-mission-control-telemetry-rho.vercel.app",
        "https://nasa-mission-control-telemetry.vercel.app",
        "http://localhost:4200",
        "http://localhost:64670",
        "http://localhost:4201"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = set()

@app.get("/telemetry/history")
async def get_history(limit: int = 100, sat_id: str = "SAT-01"):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM telemetry WHERE sat_id = :sat_id ORDER BY timestamp DESC LIMIT :limit"), 
            {"limit": limit, "sat_id": sat_id}
        )
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