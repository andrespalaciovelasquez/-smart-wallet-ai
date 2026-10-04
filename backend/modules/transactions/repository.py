from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.modules.transactions.models import Transaction

class TransactionRepository:
    """Gestiona las operaciones de lectura y escritura para la entidad Transaction"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, transaction: Transaction) -> Transaction:
        """Persiste una transacción en la base de datos (con flush para asignar id)"""
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    async def get_by_wallet_id(
        self, wallet_id: int, limit: int = 50
    ) -> Sequence[Transaction]:
        """Obtiene las transacciones asociadas a una billetera ordenadas cronológicamente"""
        stmt = (
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()