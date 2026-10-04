from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class WalletResponse(BaseModel):
    """Respuesta pública con los datos de la Billetera"""

    id: int = Field(
        description="Identificador único de la billetera", 
        examples=[1]
    )
    user_id: int = Field(
        description="Identificador único del usuario", 
        examples=[1]
    )
    balance: Decimal = Field(
        description="Saldo actual de la billetera",
        examples=[1000.00]
    )
    currency: str = Field(
        description="Código ISO 4217 de la moneda",
        examples=["USD"]
    )
    created_at: datetime = Field(
        description="Fecha de registro", 
        examples=["2026-10-04T15:00:00Z"]
    )
    updated_at: datetime = Field(
        description="Fecha de última actualización", 
        examples=["2026-10-04T15:00:00Z"]
    )

    model_config = ConfigDict(from_attributes=True)