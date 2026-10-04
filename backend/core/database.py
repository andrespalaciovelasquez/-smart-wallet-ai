from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from backend.core.config import settings

# Motor de conexión asíncrono
engine = create_async_engine(settings.DATABASE_URL, echo=settings.is_debug)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Clase base para modelos ORM
class Base(DeclarativeBase):
    """Clase base para todos los modelos de SQLAlchemy."""
    pass

# Generador de sesión para endpoints FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()