from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os, asyncio, json, ssl
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL not set!")
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/fake_db"

clean_url = DATABASE_URL.strip()
while clean_url.count("postgresql+asyncpg://") > 1:
    clean_url = clean_url.replace("postgresql+asyncpg://postgresql+asyncpg://", "postgresql+asyncpg://")

use_ssl = "supabase.com" in clean_url or "pooler.supabase.com" in clean_url or ":6543" in clean_url

for param in ["?sslmode=require", "&sslmode=require", "?pgbouncer=true", "&pgbouncer=true"]:
    clean_url = clean_url.replace(param, "")
clean_url = clean_url.replace("&&", "&").replace("?&", "?").rstrip("?&")

engine = None
try:
    connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    if use_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
    engine = create_async_engine(clean_url, echo=False, connect_args=connect_args, pool_pre_ping=True)
    print(f"Engine created ssl={use_ssl}")
except Exception as e:
    print(f"Failed: {e}")

app = FastAPI(title="NASA Mission Control API", version="2.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"status": " NASA ONLINE", "db_connected": engine is not None, "routes": ["/telemetry/latest", "/telemetry/history", "/ws/telemetry", "/health"]}

@app.get("/health")
async def health():
    if not engine:
        return {"status":"ERROR","error":"engine not created"}
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT COUNT(*) FROM telemetry"))
            count = r.scalar()
            return {"status":"OK","telemetry_count":count}
    except Exception as e:
        return {"status":"ERROR","error":str(e)}

@app.get("/telemetry/latest")
async def latest():
    if not engine:
        return {"detail": "engine not initialized"}
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1"))
            row = r.mappings().first()
            return dict(row) if row else {"detail": "no data yet"}
    except Exception as e:
        return {"detail": f"DB error: {str(e)}"}

@app.get("/telemetry/history")
async def history(limit: int = Query(100, le=20000), order: str = Query("desc"), sat_id: str = Query("SAT-01")):
    if not engine:
        return {"detail": "engine not initialized"}
    try:
        order_sql = "DESC" if order.lower() == "desc" else "ASC"
        limit = int(limit)
        async with engine.connect() as conn:
            r = await conn.execute(text(f"SELECT * FROM telemetry WHERE sat_id = :sat_id ORDER BY timestamp {order_sql} LIMIT {limit}"), {"sat_id": sat_id})
            return [dict(x) for x in r.mappings().all()]
    except Exception as e:
        return {"detail": f"DB error: {str(e)}"}

@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            async with engine.connect() as conn:
                r = await conn.execute(text("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1"))
                row = r.mappings().first()
                if row:
                    data = dict(row)
                    if isinstance(data.get("timestamp"), datetime):
                        data["timestamp"] = data["timestamp"].isoformat()
                    await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try: await websocket.close()
        except: pass
