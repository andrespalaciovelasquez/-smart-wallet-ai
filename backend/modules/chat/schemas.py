from decimal import Decimal
from pydantic import BaseModel, Field
from backend.modules.transactions.schemas import TransactionResponse


class ParseExpenseRequest(BaseModel):
    """Entrada enviada por el usuario en lenguaje natural"""
    text: str = Field(
        min_length=3,
        max_length=500,
        description="Texto libre que describe el gasto",
        examples=["Cena de sushi con amigos por $35.50"],
    )


class ExtractedExpense(BaseModel):
    """Esquema estricto para Structured Outputs con el LLM"""
    amount: Decimal = Field(
        gt=0,
        description="Monto numérico exacto del gasto detectado",
        examples=[Decimal("35.50")],
    )
    category: str = Field(
        description="Categoría del gasto (ej: Alimentación, Transporte, Salud, Entretenimiento, Servicios, Otros)",
        examples=["Alimentación"],
    )
    description: str = Field(
        description="Breve descripción o concepto del gasto",
        examples=["Cena de sushi con amigos"],
    )


class ParseExpenseResponse(BaseModel):
    """Respuesta al usuario con la transacción creada a partir del texto"""
    extracted_data: ExtractedExpense
    transaction: TransactionResponse


class ChatAskRequest(BaseModel):
    """Consulta en lenguaje natural sobre las finanzas del usuario"""
    question: str = Field(
        min_length=3,
        max_length=500,
        description="Pregunta del usuario en lenguaje natural",
        examples=["¿En qué cosas de alimentación he gastado dinero este mes?"],
    )


class ChatAskResponse(BaseModel):
    """Respuesta generada por el asistente con grounding en los datos reales"""
    question: str = Field(
        description="Pregunta original formulada por el usuario",
        examples=["¿En qué cosas de alimentación he gastado dinero este mes?"],
    )
    answer: str = Field(
        description="Respuesta analítica fundamentada en los datos reales",
        examples=["Has registrado un gasto de $35.50 en 'Cena de sushi con amigos'."],
    )
    relevant_transactions: list[TransactionResponse] = Field(
        description="Lista de transacciones recuperadas por búsqueda vectorial como evidencia",
    )
