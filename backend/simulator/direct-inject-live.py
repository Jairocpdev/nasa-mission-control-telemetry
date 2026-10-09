
import asyncio, asyncpg, os, ssl, random, time
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

# tenta .env em varios lugares
for p in [Path(".env"), Path(__file__).resolve().parents[2]/".env", Path(__file__).parent/".."/".."/".env"]:
    if p.exists():
        load_dotenv(dotenv_path=p)
        break

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set!")
    exit(1)

clean_url = DATABASE_URL.strip()
while clean_url.count("postgresql+asyncpg://") > 1:
    clean_url = clean_url.replace("postgresql+asyncpg://postgresql+asyncpg://","postgresql+asyncpg://")
while clean_url.count("postgresql://") > 1:
    clean_url = clean_url.replace("postgresql://postgresql://","postgresql://")

# para asyncpg puro
pg_url = clean_url.replace("postgresql+asyncpg://","postgresql://")
for param in ["?sslmode=require","&sslmode=require","?pgbouncer=true","&pgbouncer=true","?sslmode=prefer","&sslmode=prefer"]:
    pg_url = pg_url.replace(param,"")
pg_url = pg_url.replace("&&","&").replace("?&","?").rstrip("?&")

print(f"🔗 {pg_url[:70]}...")

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

async def get_conn():
    return await asyncpg.connect(pg_url, ssl=ssl_ctx, statement_cache_size=0, timeout=10)

async def main():
    print("🛰️ LIVE INJECTOR v2 - reconexao automatica (fix WinError 121)")
    print("🛰️ 2 msg/s - CTRL+C para parar\n")
    count=0
    while True:
        count+=1
        try:
            conn = await get_conn()
            try:
                battery = max(10, min(100, random.uniform(20,100)))
                temperature = random.uniform(-20,50)
                altitude = 400 + random.uniform(-5,20)
                signal = random.uniform(50,99)
                now = datetime.now(timezone.utc)
                await conn.execute("""
                    INSERT INTO telemetry (timestamp,sat_id,battery,temperature,altitude,signal)
                    VALUES ($1,$2,$3,$4,$5,$6)
                """, now, "SAT-01", battery, temperature, altitude, signal)
                print(f"Packet {count} -> BAT {battery:.2f}% | TEMP {temperature:.2f}C | ALT {altitude:.2f}km | SIG {signal:.1f}% @ {now.strftime('%H:%M:%S')}")
            finally:
                await conn.close()
        except Exception as e:
            print(f"⚠️ Retry in 2s: {e}")
            await asyncio.sleep(2)
            continue
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
