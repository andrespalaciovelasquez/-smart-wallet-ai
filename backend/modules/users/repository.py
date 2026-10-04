from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.users.models import User

class UserRepository:
    """Gestiona las operaciones de lectura y escritura para la entidad User"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        """Busca un usuario por su correo electrónico"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> User | None:
        """Busca un usuario por su identificador único"""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persiste una nueva entidad User en la base de datos"""
        self.session.add(user)
        await self.session.flush()  # Asigna el ID autoincremental sin hacer commit definitivo
        await self.session.refresh(user)
        return user