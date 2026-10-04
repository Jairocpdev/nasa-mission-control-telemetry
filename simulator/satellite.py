import time
import json
import random
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

sat_id = "SAT-01"

while True:
    packet = {
        "sat_id": sat_id,
        "timestamp": time.time(),
        "battery": round(random.uniform(20, 100), 2), # 20% a 100%
        "temperature": round(random.uniform(-50, 80), 2),
        "altitude": round(random.uniform(400, 450), 2),
        "signal": round(random.uniform(0, 100), 2)
    }
    r.publish("telemetry", json.dumps(packet))
    print(f"📡 {sat_id} -> {packet}")
    time.sleep(0.5) # 2 msg/s