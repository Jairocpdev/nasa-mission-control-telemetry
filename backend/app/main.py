from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os, asyncio, json
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0}
)

app = FastAPI(title="NASA Mission Control API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": " NASA ONLINE", "routes": ["/telemetry/latest", "/telemetry/history", "/ws/telemetry"]}

@app.get("/telemetry/latest")
async def latest():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1"))
        row = r.mappings().first()
        return dict(row) if row else {"detail": "no data yet - run satellite.py"}

@app.get("/telemetry/history")
async def history(limit: int = Query(100, le=20000), order: str = Query("desc"), sat_id: str = Query("SAT-01")):
    order_sql = "DESC" if order.lower() == "desc" else "ASC"
    limit = int(limit)
    async with engine.connect() as conn:
        r = await conn.execute(
            text(f"SELECT * FROM telemetry WHERE sat_id = :sat_id ORDER BY timestamp {order_sql} LIMIT {limit}"),
            {"sat_id": sat_id}
        )
        return [dict(x) for x in r.mappings().all()]

@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    print(f"🛰️ WS Client connected: {websocket.client}")
    try:
        while True:
            async with engine.connect() as conn:
                r = await conn.execute(text("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1"))
                row = r.mappings().first()
                if row:
                    data = dict(row)
                    # converte datetime pra ISO se precisar
                    if isinstance(data.get("timestamp"), datetime):
                        data["timestamp"] = data["timestamp"].isoformat()
                    await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print(f"WS Client disconnected: {websocket.client}")
    except Exception as e:
        print(f"WS Error: {e}")
        await websocket.close()