import asyncio, json, os
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = create_async_engine(DATABASE_URL, echo=False)

async def listen():
    r = redis.from_url(REDIS_URL, decode_responses=True, ssl_cert_reqs="none")
    pubsub = r.pubsub()
    await pubsub.subscribe("telemetry")
    print("👂 Ingestor listening on cloud...")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            async with engine.begin() as conn:
                await conn.execute(text("""
                    INSERT INTO telemetry (timestamp, sat_id, battery, temperature, altitude, signal)
                    VALUES (NOW(), :sat_id, :battery, :temperature, :altitude, :signal)
                """), {
                    "sat_id": data.get("sat_id", "SAT-01"),
                    "battery": data.get("battery"),
                    "temperature": data.get("temperature"),
                    "altitude": data.get("altitude"),
                    "signal": data.get("signal")
                })
            print(f"Ingested battery={data.get('battery'):.1f}")

if __name__ == "__main__":
    asyncio.run(listen())