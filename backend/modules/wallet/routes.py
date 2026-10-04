from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.modules.users.models import User
from backend.modules.wallet.schemas import WalletResponse
from backend.modules.wallet.services import WalletService

router = APIRouter(prefix="/wallet", tags=["Wallet"])

def get_wallet_service(session: AsyncSession = Depends(get_db)) -> WalletService:
    """Proveedor de dependencia para inyectar WalletService"""
    return WalletService(session=session)

@router.get(
    "/me",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar billetera del usuario autenticado",
    description="Devuelve el saldo actual y los detalles de la billetera del usuario autenticado mediante Bearer Token.",
)
async def get_my_wallet(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    """Endpoint protegido que retorna los detalles de la billetera del usuario en sesión"""
    wallet = await wallet_service.get_wallet(current_user=current_user)
    return wallet