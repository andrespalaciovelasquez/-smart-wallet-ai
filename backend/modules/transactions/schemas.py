from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from backend.modules.transactions.models import TransactionType

class TransactionCreate(BaseModel):
    """Esquema de entrada para registrar un movimiento financiero"""
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Monto monetario de la transacción (debe ser mayor a 0)",
        examples=[45.50],
    )
    type: TransactionType = Field(
        description="Tipo de movimiento: INCOME (Ingreso) o EXPENSE (Gasto)",
        examples=[TransactionType.EXPENSE],
    )
    category: str = Field(
        min_length=2,
        max_length=50,
        description="Categoría del movimiento",
        examples=["Alimentación"],
    )
    description: str = Field(
        min_length=3,
        max_length=255,
        description="Descripción o concepto del movimiento",
        examples=["Cena en restaurante"],
    )


class TransactionResponse(BaseModel):
    """Respuesta pública con los detalles de una transacción"""
    id: int = Field(
        description="Identificador único de la transacción", 
        examples=[1]
    )
    wallet_id: int = Field(
        description="Identificador de la billetera asociada", 
        examples=[1]
    )
    amount: Decimal = Field(
        description="Monto de la transacción", 
        examples=[45.50]
    )
    type: TransactionType = Field(
        description="Tipo de transacción", 
        examples=[TransactionType.EXPENSE]
    )
    category: str = Field(
        description="Categoría", 
        examples=["Alimentación"]
    )
    description: str = Field(
        description="Descripción o concepto", 
        examples=["Cena en restaurante"]
    )
    created_at: datetime = Field(description="Fecha y hora de registro")

    model_config = ConfigDict(from_attributes=True)