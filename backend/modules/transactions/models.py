import enum
from datetime import datetime, timezone
from decimal import Decimal
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.config import settings
from backend.core.database import Base

class TransactionType(str, enum.Enum):
    """Tipos de transacción permitidos en el sistema"""
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class Transaction(Base):
    """Representa la tabla 'transactions' en la base de datos"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2))
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, 
        name="transaction_type_enum"), 
        index=True
    )
    category: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(String(255))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        index=True
    )