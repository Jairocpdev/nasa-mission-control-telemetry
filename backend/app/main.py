from fastapi import FastAPI

app = FastAPI(title="Mission Control Telemetry")

@app.get("/")
def health_check():
    return {"status": "NOMINAL", "mission": "Mission Control is GO"}