from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.wallet.models import Wallet

class WalletRepository:
    """Gestiona las operaciones de lectura y escritura para la entidad Wallet"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def get_by_user_id(self, user_id: int) -> Wallet | None:
        """Obtiene la Billetera de un usuario por su ID"""
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()