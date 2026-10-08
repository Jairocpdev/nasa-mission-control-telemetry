import os, json, random, time
from datetime import datetime, timezone
import redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
print(f"Conectando em {REDIS_URL[:50]}...")
r = redis.from_url(REDIS_URL, decode_responses=True, ssl_cert_reqs=None, ssl_check_hostname=False)
print("🛰  SAT-01 publishing...")
while True:
    packet = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sat_id": "SAT-01",
        "battery": round(random.uniform(20, 100), 2),
        "temperature": round(random.uniform(-50, 50), 2),
        "altitude": round(random.uniform(400, 420), 2),
        "signal": round(random.uniform(0, 100), 2)
    }
    r.publish("telemetry", json.dumps(packet))
    print(f"Sent {packet['battery']}%")
    time.sleep(0.5)
