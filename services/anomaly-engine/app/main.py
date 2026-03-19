from fastapi import FastAPI
import os

app = FastAPI(title="anomaly-engine Service")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "anomaly-engine"}
