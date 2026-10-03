from fastapi import FastAPI
from backend.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
async def root():
    return {"message": "Smart Wallet AI is running"}