import asyncio
from sqlalchemy import text
from app.database import engine, Base
from app.models.telemetry import Telemetry

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        await conn.execute(text("""
            SELECT create_hypertable('telemetry', 'timestamp', 
                                     if_not_exists => TRUE,
                                     chunk_time_interval => INTERVAL '1 day');
        """))
        print("✅ Hypertable created")
        
        # SEPARADO - era isso que quebrou
        await conn.execute(text("""
            ALTER TABLE telemetry SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'sat_id'
            );
        """))
        
        # SEPARADO - segundo comando separado
        await conn.execute(text("""
            SELECT add_compression_policy('telemetry', INTERVAL '7 days', if_not_exists => TRUE);
        """))
        print("✅ Compression policy created")
        
    print("✅ Mission Control is ready for 5M rows/month")

if __name__ == "__main__":
    asyncio.run(init())