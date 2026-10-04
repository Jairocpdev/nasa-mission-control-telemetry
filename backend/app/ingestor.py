import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionLocal
from app.models.telemetry import Telemetry
from datetime import datetime, timezone

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

connected_clients = set()

async def save_to_db(packet: dict):
    async with SessionLocal() as session:

        tel = Telemetry ( 
            timestamp=datetime.fromtimestamp(packet['timestamp'], tz=timezone.utc),
            sat_id=packet['sat_id'],
            battery=packet['battery'],
            temperature=packet['temperature'],
            altitude=packet['altitude'],
            signal=packet['signal']
        )

        session.add(tel)
        await session.commit()

async def listen():
    pubsub = r.pubsub()
    await pubsub.subscribe("telemetry")
    print("👂 Ingestor listening on Redis channel 'telemetry'")
    
    async for message in pubsub.listen():
        if message['type'] == 'message':
            packet = json.loads(message['data'])

            await save_to_db(packet)
            
            for ws in list(connected_clients):
                try:
                    await ws.send_json(packet)
                except:
                    connected_clients.discard(ws)
            
            status = "🔴 CRITICAL" if packet['battery'] < 20 or packet['temperature'] > 75 else "🟢 NOMINAL"
            print(f"{status} | {packet['sat_id']} | Batt: {packet['battery']}% | Temp: {packet['temperature']}°C")

if __name__ == "__main__":
    asyncio.run(listen())