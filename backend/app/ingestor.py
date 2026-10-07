import asyncio
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/mission_control")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def save_to_db(packet):
    ts_str = packet['timestamp']
    timestamp = datetime.fromisoformat(ts_str.replace('Z',''))

    if timestamp.tzinfo is not None:
        timestamp = timestamp.replace(tzinfo=None)

    async with AsyncSessionLocal() as session:
        query = text("""
            INSERT INTO telemetry (timestamp, sat_id, battery, temperature, altitude, signal)
            VALUES (:timestamp, :sat_id, :battery, :temperature, :altitude, :signal)
        """)
        await session.execute(query, {
            "timestamp": timestamp,
            "sat_id": packet['sat_id'],
            "battery": packet['battery'],
            "temperature": packet['temperature'],
            "altitude": packet['altitude'],
            "signal": packet['signal']
        })
        await session.commit()
        print(f"💾 Saved: {packet['sat_id']} battery={packet['battery']}%")

async def listen():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("telemetry")
    print("👂 Ingestor listening on Redis channel 'telemetry'")
    
    async for message in pubsub.listen():
        if message['type'] == 'message':
            packet = json.loads(message['data'])
            await save_to_db(packet)

if __name__ == "__main__":
    asyncio.run(listen())