import asyncio
import json
import random
from datetime import datetime
import redis.asyncio as redis

async def main():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    print("🛰️  SAT-01 publishing telemetry 2msg/s to Redis...")
    sat_id = "SAT-01"
    while True:
        packet = {
            "timestamp": datetime.utcnow().isoformat(),
            "sat_id": sat_id,
            "battery": round(random.uniform(10, 100), 2),
            "temperature": round(random.uniform(-50, 80), 2),
            "altitude": round(random.uniform(400, 450), 2),
            "signal": round(random.uniform(5, 100), 2)
        }
        await r.publish("telemetry", json.dumps(packet))
        print(f"📡 {packet}")
        await asyncio.sleep(0.5)  # 2msg/s

if __name__ == "__main__":
    asyncio.run(main())