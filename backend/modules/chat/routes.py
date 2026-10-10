from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.modules.chat.schemas import ChatAskRequest, ChatAskResponse, ParseExpenseRequest, ParseExpenseResponse
from backend.modules.chat.services import ChatService
from backend.modules.users.models import User

router = APIRouter(prefix="/chat", tags=["Chat & IA"])


def get_chat_service(
    session: AsyncSession = Depends(get_db),
) -> ChatService:
    """Inyector de dependencias para instanciar ChatService con la sesión de DB"""
    return ChatService(session=session)


@router.post(
    "/parse-expense",
    response_model=ParseExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar gasto desde lenguaje natural (Structured Outputs)",
    description=(
        "Recibe texto libre describiendo un gasto (ej: 'Ayer cené ramen por $38.50'), "
        "utiliza el LLM con Structured Outputs tipados en Pydantic para extraer monto, "
        "categoría y concepto, descuenta el saldo de la billetera y genera su vector en pgvector."
    ),
)
async def parse_expense(
    payload: ParseExpenseRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ParseExpenseResponse:
    """Extrae un gasto con IA y lo registra atómicamente en la billetera"""
    return await chat_service.parse_expense(
        current_user=current_user,
        text=payload.text,
    )


@router.post(
    "/ask",
    response_model=ChatAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar al asistente financiero (RAG con pgvector)",
    description=(
        "Recibe una pregunta en lenguaje natural sobre las finanzas del usuario, "
        "genera el embedding de la consulta, ejecuta una búsqueda por similitud semántica (KNN) "
        "con distancia coseno en pgvector sobre las transacciones del usuario, "
        "ensambla un Prompt Compositivo y genera una respuesta grounded y verificable."
    ),
)
async def ask_financial_assistant(
    payload: ChatAskRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatAskResponse:
    """Responde consultas financieras fundamentadas en datos reales mediante RAG"""
    return await chat_service.ask_financial_assistant(
        current_user=current_user,
        question=payload.question,
    )