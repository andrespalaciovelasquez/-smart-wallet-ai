"""Pruebas unitarias para el asistente financiero RAG (ChatService.ask_financial_assistant)"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pytest_mock import MockerFixture
from backend.errors.exceptions import WalletNotFoundError
from backend.modules.chat.services import ChatService
from backend.modules.transactions.models import Transaction, TransactionType
from backend.modules.users.models import User
from backend.modules.wallet.models import Wallet


async def test_ask_financial_assistant_success(
    mock_user: User, mock_wallet: Wallet, mocker: MockerFixture
):
    """Valida el pipeline RAG completo: embedding -> búsqueda vectorial -> prompt compositivo -> respuesta grounded"""
    # Arrange
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = mock_wallet

    # Simular una transacción previa recuperada por similitud en pgvector
    mock_tx = Transaction(
        id=1,
        wallet_id=mock_wallet.id,
        amount=Decimal("45.00"),
        type=TransactionType.EXPENSE,
        category="Salud",
        description="Farmacia San Pablo",
        embedding=[0.1] * 768,
        created_at=datetime.now(timezone.utc),
    )
    mock_tx_repo = mocker.AsyncMock()
    mock_tx_repo.search_semantic.return_value = [mock_tx]

    # Simular el cliente LLM (vectorización y generación de respuesta)
    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_embedding.return_value = [0.1] * 768
    mock_llm_client.generate_text.return_value = (
        "Has gastado un total de $45.00 en Salud, correspondiente a una compra en Farmacia San Pablo."
    )

    chat_service = ChatService(
        session=mock_session,
        wallet_repo=mock_wallet_repo,
        transaction_repo=mock_tx_repo,
        llm_client=mock_llm_client,
    )

    # Act
    question = "¿Cuánto gasté en salud este mes?"
    response = await chat_service.ask_financial_assistant(
        current_user=mock_user,
        question=question,
        limit=5,
    )

    # Assert
    assert response.question == question
    assert "Farmacia San Pablo" in response.answer
    assert len(response.relevant_transactions) == 1
    assert response.relevant_transactions[0].id == 1
    assert response.relevant_transactions[0].amount == Decimal("45.00")

    # Verificar que se generó el embedding de la pregunta
    mock_llm_client.generate_embedding.assert_awaited_once_with(question)

    # Verificar que se buscó en pgvector para la billetera del usuario
    mock_tx_repo.search_semantic.assert_awaited_once_with(
        wallet_id=mock_wallet.id,
        query_embedding=[0.1] * 768,
        limit=5,
    )


async def test_ask_financial_assistant_no_wallet_raises_error(
    mock_user: User, mocker: MockerFixture
):
    """Valida que si el usuario no tiene billetera se arroje WalletNotFoundError"""
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = None

    chat_service = ChatService(
        session=mock_session,
        wallet_repo=mock_wallet_repo,
    )

    with pytest.raises(WalletNotFoundError):
        await chat_service.ask_financial_assistant(
            current_user=mock_user,
            question="¿Cuál es mi saldo?",
        )


async def test_ask_financial_assistant_without_history(
    mock_user: User, mock_wallet: Wallet, mocker: MockerFixture
):
    """Valida el comportamiento RAG cuando el usuario aún no tiene transacciones sobre ese tema"""
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = mock_wallet

    mock_tx_repo = mocker.AsyncMock()
    mock_tx_repo.search_semantic.return_value = []  # Sin transacciones

    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_embedding.return_value = [0.2] * 768
    mock_llm_client.generate_text.return_value = (
        "No encontré registros de gastos en viajes en tu historial."
    )

    chat_service = ChatService(
        session=mock_session,
        wallet_repo=mock_wallet_repo,
        transaction_repo=mock_tx_repo,
        llm_client=mock_llm_client,
    )

    response = await chat_service.ask_financial_assistant(
        current_user=mock_user,
        question="¿Cuánto he gastado en viajes?",
    )

    assert len(response.relevant_transactions) == 0
    assert "No encontré registros" in response.answer