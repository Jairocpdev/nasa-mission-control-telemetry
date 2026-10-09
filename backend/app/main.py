from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0}
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": " NASA ONLINE", "routes": ["/telemetry/latest", "/telemetry/history"]}

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