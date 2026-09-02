from fastapi import FastAPI
from services.api.health import get_health_status

app = FastAPI(title="ATS Resume Generator API")


@app.get("/health")
def health():
    return get_health_status()