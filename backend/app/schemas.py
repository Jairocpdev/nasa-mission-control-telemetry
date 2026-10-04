from pydantic import BaseModel

class TelemetryPacket(BaseModel):
    sat_id: str
    timestamp: float
    battery: float
    temperature: float
    altitude: float
    signal: float

    def is_critical(self):
        return self.battery < 20 or self.temperature > 75 or self.temperature < -40