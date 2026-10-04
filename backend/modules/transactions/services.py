from collections.abc import Sequence
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.llm import LLMClient
from backend.errors.exceptions import InsufficientBalanceError, WalletNotFoundError
from backend.modules.users.models import User
from backend.modules.wallet.repository import WalletRepository
from backend.modules.transactions.models import Transaction, TransactionType
from backend.modules.transactions.repository import TransactionRepository
from backend.modules.transactions.schemas import TransactionCreate

logger = logging.getLogger(__name__)

class TransactionService:
    """Orquesta las operaciones financieras y el enriquecimiento semántico de transacciones"""

    def __init__(
        self,
        session: AsyncSession,
        transaction_repo: TransactionRepository | None = None,
        wallet_repo: WalletRepository | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.session = session
        self.transaction_repo = transaction_repo or TransactionRepository(session)
        self.wallet_repo = wallet_repo or WalletRepository(session)
        self.llm_client = llm_client or LLMClient()

    async def create_transaction(
        self, current_user: User, data: TransactionCreate
    ) -> Transaction:
        """Crea una transacción, actualiza el saldo de la billetera y genera embeddings con IA"""
        wallet = await self.wallet_repo.get_by_user_id(current_user.id)
        if wallet is None:
            raise WalletNotFoundError("Billetera no encontrada para el usuario actual")

        #  Aplicar reglas de saldo
        if data.type == TransactionType.EXPENSE:
            if wallet.balance < data.amount:
                raise InsufficientBalanceError(
                    f"Saldo insuficiente. Saldo disponible: {wallet.balance} {wallet.currency}, monto requerido: {data.amount}"
                )
            wallet.balance -= data.amount
        elif data.type == TransactionType.INCOME:
            wallet.balance += data.amount

        # Generación de embedding con IA (resiliente a fallos)
        embedding: list[float] | None = None
        try:
            semantic_text = f"{data.category}: {data.description}"
            embedding = await self.llm_client.generate_embedding(semantic_text)
        except Exception as err:
            logger.warning(
                "No se pudo generar el embedding para la transacción: %s. Se guardará sin vector.",
                err,
            )

        # Crear entidad y persistir
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=data.amount,
            type=data.type,
            category=data.category,
            description=data.description,
            embedding=embedding,
        )
        transaction = await self.transaction_repo.create(transaction)

        # Commit atómico (saldo de wallet + transacción juntos)
        await self.session.commit()
        await self.session.refresh(transaction)

        return transaction

    async def get_user_transactions(
        self, current_user: User, limit: int = 50
    ) -> Sequence[Transaction]:
        """Recupera el historial de transacciones de la billetera del usuario"""
        wallet = await self.wallet_repo.get_by_user_id(current_user.id)
        if wallet is None:
            raise WalletNotFoundError("Billetera no encontrada para el usuario actual")

        return await self.transaction_repo.get_by_wallet_id(wallet.id, limit=limit)