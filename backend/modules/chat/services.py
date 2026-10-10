from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.llm import LLMClient
from backend.errors.exceptions import WalletNotFoundError
from backend.modules.chat.prompts import EXPENSE_PARSER_SYSTEM_PROMPT, FINANCIAL_ADVISOR_SYSTEM_PROMPT, FinancialPromptBuilder
from backend.modules.chat.schemas import ChatAskResponse, ExtractedExpense, ParseExpenseResponse
from backend.modules.transactions.models import Transaction, TransactionType
from backend.modules.transactions.repository import TransactionRepository
from backend.modules.transactions.schemas import TransactionCreate, TransactionResponse
from backend.modules.transactions.services import TransactionService
from backend.modules.users.models import User
from backend.modules.wallet.repository import WalletRepository


class ChatService:
    """Orquesta las capacidades de IA conversacional, extracción estructurada y RAG financiero"""

    def __init__(
        self,
        session: AsyncSession,
        transaction_service: TransactionService | None = None,
        transaction_repo: TransactionRepository | None = None,
        wallet_repo: WalletRepository | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.session = session
        self.transaction_service = transaction_service or TransactionService(session)
        self.transaction_repo = transaction_repo or TransactionRepository(session)
        self.wallet_repo = wallet_repo or WalletRepository(session)
        self.llm_client = llm_client or LLMClient()

    async def parse_expense(
        self, current_user: User, text: str
    ) -> ParseExpenseResponse:
        """Extrae los datos de un gasto con Structured Outputs y lo registra en la billetera"""
        # Extracción estructurada determinista con OpenAI SDK
        extracted: ExtractedExpense = await self.llm_client.generate_structured(
            prompt=text,
            response_schema=ExtractedExpense,
            system_instruction=EXPENSE_PARSER_SYSTEM_PROMPT,
        )

        # Registrar la transacción aplicando las reglas financieras de dominio
        tx_create = TransactionCreate(
            amount=extracted.amount,
            type=TransactionType.EXPENSE,
            category=extracted.category,
            description=extracted.description,
        )
        created_tx = await self.transaction_service.create_transaction(
            current_user=current_user,
            data=tx_create,
        )

        return ParseExpenseResponse(
            extracted_data=extracted,
            transaction=TransactionResponse.model_validate(created_tx),
        )

    async def ask_financial_assistant(
        self, current_user: User, question: str, limit: int = 5
    ) -> ChatAskResponse:
        """Responde preguntas financieras usando RAG (Embeddings + pgvector + Prompt Compositivo)"""
        # Validar billetera del usuario en sesión
        wallet = await self.wallet_repo.get_by_user_id(current_user.id)
        if wallet is None:
            raise WalletNotFoundError("Billetera no encontrada para el usuario actual")

        # Vectorizar la consulta del usuario
        query_embedding = await self.llm_client.generate_embedding(question)

        # Búsqueda por similitud semántica en pgvector (distancia coseno)
        relevant_txs: Sequence[Transaction] = await self.transaction_repo.search_semantic(
            wallet_id=wallet.id,
            query_embedding=query_embedding,
            limit=limit,
        )

        # Ensamblar prompt compositivo con la capa de prompts de dominio
        composite_prompt = FinancialPromptBuilder.build_rag_prompt(
            balance=wallet.balance,
            currency=wallet.currency,
            transactions=relevant_txs,
            question=question,
        )

        # Generar respuesta fundamentada (grounded)
        answer = await self.llm_client.generate_text(
            prompt=composite_prompt,
            system_instruction=FINANCIAL_ADVISOR_SYSTEM_PROMPT,
            temperature=0.2,
        )

        return ChatAskResponse(
            question=question,
            answer=answer,
            relevant_transactions=[
                TransactionResponse.model_validate(tx) for tx in relevant_txs
            ],
        )