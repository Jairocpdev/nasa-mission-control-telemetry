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

# Render precisa de DATABASE_URL nas Environment Variables, não só no .env
if not DATABASE_URL:
    print("⚠️  WARNING: DATABASE_URL not set! Check Render Environment Variables")
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/fake_db"

# --- FIX Supabase + asyncpg: asyncpg não entende ?sslmode=require na URL ---
# Se a URL vier com sslmode, pgbouncer, etc, a gente limpa e usa ssl=True no connect_args
clean_url = DATABASE_URL.strip()
use_ssl = False

# FIX: se colou 2x o prefixo (postgresql+asyncpg://postgresql+asyncpg://...) corrige
while clean_url.count("postgresql+asyncpg://") > 1:
    clean_url = clean_url.replace("postgresql+asyncpg://postgresql+asyncpg://", "postgresql+asyncpg://")
while clean_url.count("postgresql://") > 1:
    clean_url = clean_url.replace("postgresql://postgresql://", "postgresql://")

if "supabase.com" in clean_url or "sslmode=require" in clean_url or "sslmode" in clean_url:
    use_ssl = True
    # remove parametros que quebram asyncpg
    clean_url = clean_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    clean_url = clean_url.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")
    clean_url = clean_url.replace("&&", "&").replace("?&", "?")
    clean_url = clean_url.rstrip("?&")
    print(f"🔧 Supabase detected, using SSL=True, cleaned URL")
else:
    # Mesmo sem supabase.com, se for pooler precisa SSL
    if "pooler.supabase.com" in clean_url or ":6543" in clean_url:
        use_ssl = True

engine = None
try:
    connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    if use_ssl:
        connect_args["ssl"] = True

    engine = create_async_engine(
        clean_url,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    print(f"✅ Engine created for DB: {clean_url[:35]}... ssl={use_ssl}")
except Exception as e:
    print(f"❌ Failed to create engine: {e}")

app = FastAPI(title="NASA Mission Control API", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": " NASA ONLINE", "db_connected": engine is not None, "routes": ["/telemetry/latest", "/telemetry/history", "/ws/telemetry", "/health"]}

@app.get("/health")
async def health():
    if not engine:
        return {"status":"ERROR","error":"engine not created, check DATABASE_URL env var"}
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT COUNT(*) FROM telemetry"))
            count = r.scalar()
            return {"status":"OK","telemetry_count":count,"database_url_set": bool(os.getenv("DATABASE_URL"))}
    except Exception as e:
        return {"status":"ERROR","error":str(e),"hint":"Check DATABASE_URL, maybe need ?sslmode=require"}

@app.get("/telemetry/latest")
async def latest():
    if not engine:
        return {"detail": "engine not initialized - DATABASE_URL missing"}
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1"))
            row = r.mappings().first()
            return dict(row) if row else {"detail": "no data yet - run satellite.py"}
    except Exception as e:
        print(f"❌ /latest error: {e}")
        return {"detail": f"DB error: {str(e)}", "hint": "Check if table telemetry exists, run CREATE TABLE"}

@app.get("/telemetry/history")
async def history(limit: int = Query(100, le=20000), order: str = Query("desc"), sat_id: str = Query("SAT-01")):
    if not engine:
        return {"detail": "engine not initialized"}
    try:
        order_sql = "DESC" if order.lower() == "desc" else "ASC"
        limit = int(limit)
        async with engine.connect() as conn:
            r = await conn.execute(
                text(f"SELECT * FROM telemetry WHERE sat_id = :sat_id ORDER BY timestamp {order_sql} LIMIT {limit}"),
                {"sat_id": sat_id}
            )
            return [dict(x) for x in r.mappings().all()]
    except Exception as e:
        print(f"❌ /history error: {e}")
        return {"detail": f"DB error: {str(e)}"}

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
