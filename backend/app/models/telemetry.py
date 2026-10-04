from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
import datetime

class Telemetry(Base):
    __tablename__ = "telemetry"

    timestamp = Column(DateTime, primary_key=True, default=datetime.datetime.utcnow)
    sat_id = Column(String, primary_key=True)
    battery = Column(Float)
    temperature = Column(Float)
    altitude = Column(Float)
    signal = Column(Float)