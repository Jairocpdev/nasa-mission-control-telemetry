import asyncio, random, os
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / '.env')

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, connect_args={"statement_cache_size":0,"prepared_statement_cache_size":0})

async def main():
    print("🛰️  LIVE INJECTOR - TimescaleDB direct (sem Redis)")
    print("🛰️  2 msg/s igual satellite.py original - CTRL+C para parar\n")
    count = 0
    while True:
        count += 1
        # Cada loop abre e fecha sua própria transação - sem commit manual
        async with engine.begin() as conn:
            packet = {
                "timestamp": datetime.now(timezone.utc),
                "sat_id": "SAT-01",
                "battery": random.uniform(20,100),
                "temperature": random.uniform(-20,50),
                "altitude": random.uniform(400,420),
                "signal": random.uniform(20,100),
            }
            await conn.execute(text("INSERT INTO telemetry (timestamp,sat_id,battery,temperature,altitude,signal) VALUES (:timestamp,:sat_id,:battery,:temperature,:altitude,:signal)"), packet)
        print(f"Packet {count} -> Battery {packet['battery']:.2f}% | Temp {packet['temperature']:.2f}°C | Alt {packet['altitude']:.2f}km")
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())