import asyncio, json, os, random
from datetime import datetime, timezone
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def main():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    print(f"🛰  SAT-01 publishing to {REDIS_URL[-30:]}")
    while True:
        packet = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sat_id": "SAT-01",
            "battery": random.uniform(20, 100),
            "temperature": random.uniform(-50, 50),
            "altitude": random.uniform(400, 420),
            "signal": random.uniform(0, 100)
        }
        await r.publish("telemetry", json.dumps(packet))
        print(f"Sent battery {packet['battery']:.1f}%")
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())