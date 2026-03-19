from fastapi import FastAPI
import os

app = FastAPI(title="aggregation-service Service")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "aggregation-service"}
