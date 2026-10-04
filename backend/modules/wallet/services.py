from sqlalchemy.ext.asyncio import AsyncSession

from backend.errors.exceptions import WalletNotFoundError
from backend.modules.users.models import User
from backend.modules.wallet.models import Wallet
from backend.modules.wallet.repository import WalletRepository


class WalletService:
    """Orquesta la lógica de negocio para la billetera del usuario"""

    def __init__(self, session: AsyncSession) -> None:
        self.wallet_repo = WalletRepository(session)

    async def get_wallet(self, current_user: User) -> Wallet:
        """Obtiene la billetera del usuario autenticado"""
        wallet = await self.wallet_repo.get_by_user_id(current_user.id)

        if wallet is None:
            raise WalletNotFoundError(
                f"No se encontró una billetera para el usuario {current_user.email}"
            )

        return wallet