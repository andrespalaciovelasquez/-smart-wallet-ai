from collections.abc import Sequence
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.modules.users.models import User
from backend.modules.transactions.schemas import TransactionCreate, TransactionResponse
from backend.modules.transactions.services import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_transaction_service(
    session: AsyncSession = Depends(get_db),
) -> TransactionService:
    """Proveedor de dependencia para inyectar TransactionService en las rutas"""
    return TransactionService(session=session)


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva transacción",
    description="Registra un ingreso o gasto, actualiza el saldo de la billetera y genera un embedding semántico con IA.",
)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Crea una transacción y descuenta/abona al saldo de la billetera"""
    transaction = await transaction_service.create_transaction(
        current_user=current_user, data=payload
    )
    return transaction


@router.get(
    "/",
    response_model=list[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar transacciones del usuario",
    description="Devuelve el historial de transacciones del usuario autenticado ordenadas por fecha reciente.",
)
async def list_transactions(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Cantidad máxima de registros a recuperar",
    ),
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> Sequence[TransactionResponse]:
    """Recupera el historial de movimientos de la billetera del usuario en sesión"""
    transactions = await transaction_service.get_user_transactions(
        current_user=current_user, limit=limit
    )
    return transactions