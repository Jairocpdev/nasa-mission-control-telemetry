import asyncio, json, os
from datetime import datetime
from dotenv import load_dotenv
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)

async def listen():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("telemetry")
    print("👂 Ingestor listening...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])

            # FIX: converte string ISO -> datetime
            ts = data.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))

            async with engine.begin() as conn:
                await conn.execute(text("""
                    INSERT INTO telemetry (timestamp, sat_id, battery, temperature, altitude, signal)
                    VALUES (:timestamp, :sat_id, :battery, :temperature, :altitude, :signal)
                """), {
                    "timestamp": ts,
                    "sat_id": data.get("sat_id", "SAT-01"),
                    "battery": data.get("battery"),
                    "temperature": data.get("temperature"),
                    "altitude": data.get("altitude"),
                    "signal": data.get("signal")
                })
            print(f"✅ Ingested {ts} battery={data.get('battery'):.1f}")

if __name__ == "__main__":
    asyncio.run(listen())