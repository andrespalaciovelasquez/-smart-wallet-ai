from fastapi import FastAPI

app = FastAPI(title="Smart Wallet AI")

@app.get("/")
async def root():
    return {"message": "Smart Wallet AI is running"}