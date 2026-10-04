from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.core.database import engine, Base, get_db
from backend.modules.users.models import User  # noqa: F401
from backend.modules.wallet.models import Wallet  # noqa: F401
from backend.errors.handlers import register_exception_handlers
from backend.modules.users.routes import router as users_router
from backend.modules.wallet.routes import router as wallet_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield

    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.is_debug,
    lifespan=lifespan
)

# Registrar interceptores globales de error
register_exception_handlers(app)

# Registrar routers de módulos
app.include_router(users_router)
app.include_router(wallet_router)

@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.APP_ENV,
    }