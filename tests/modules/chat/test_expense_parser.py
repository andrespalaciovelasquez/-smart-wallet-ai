"""Pruebas unitarias para el extractor de gastos en lenguaje natural (ChatService.parse_expense)"""

from decimal import Decimal
import pytest
from pytest_mock import MockerFixture
from datetime import datetime, timezone
from backend.errors.exceptions import InsufficientBalanceError
from backend.modules.chat.schemas import ExtractedExpense
from backend.modules.chat.services import ChatService
from backend.modules.transactions.models import Transaction, TransactionType
from backend.modules.transactions.schemas import TransactionCreate
from backend.modules.users.models import User


async def test_parse_expense_success(mock_user: User, mocker: MockerFixture):
    """Verifica que el servicio procese la salida estructurada del LLM y cree la transacción"""
    # Arrange: Simular la respuesta estructurada del LLM con pytest-mock
    mock_extracted = ExtractedExpense(
        amount=Decimal("35.50"),
        category="Alimentación",
        description="Cena de sushi con amigos",
    )
    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_structured.return_value = mock_extracted

    # Simular la creación exitosa en el TransactionService
    mock_created_tx = Transaction(
        id=10,
        wallet_id=1,
        amount=mock_extracted.amount,
        type=TransactionType.EXPENSE,
        category=mock_extracted.category,
        description=mock_extracted.description,
        embedding=[0.1] * 768,
        created_at=datetime.now(timezone.utc)
    )
    mock_tx_service = mocker.AsyncMock()
    mock_tx_service.create_transaction.return_value = mock_created_tx

    mock_session = mocker.AsyncMock()
    chat_service = ChatService(
        session=mock_session,
        transaction_service=mock_tx_service,
        llm_client=mock_llm_client,
    )

    # Act: Ejecutar la extracción del gasto
    response = await chat_service.parse_expense(
        current_user=mock_user,
        text="Ayer cené sushi por 35.50 con unos amigos",
    )

    # Assert: Validar datos retornados
    assert response.extracted_data.amount == Decimal("35.50")
    assert response.extracted_data.category == "Alimentación"
    assert response.transaction.id == 10
    assert response.transaction.amount == Decimal("35.50")

    # Verificar que el LLM fue invocado
    mock_llm_client.generate_structured.assert_awaited_once()

    # Verificar que TransactionService recibió los datos tipados de dominio
    mock_tx_service.create_transaction.assert_awaited_once_with(
        current_user=mock_user,
        data=TransactionCreate(
            amount=Decimal("35.50"),
            type=TransactionType.EXPENSE,
            category="Alimentación",
            description="Cena de sushi con amigos",
        ),
    )


async def test_parse_expense_insufficient_balance(
    mock_user: User, mocker: MockerFixture
):
    """Verifica que si el gasto supera el saldo disponible, se propague InsufficientBalanceError"""
    mock_extracted = ExtractedExpense(
        amount=Decimal("5000.00"),
        category="Lujos",
        description="Reloj de oro",
    )
    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_structured.return_value = mock_extracted

    # Simular que TransactionService rechaza la operación por falta de fondos
    mock_tx_service = mocker.AsyncMock()
    mock_tx_service.create_transaction.side_effect = InsufficientBalanceError(
        "Saldo insuficiente. Saldo disponible: 1000.00 USD, monto requerido: 5000.00"
    )

    mock_session = mocker.AsyncMock()
    chat_service = ChatService(
        session=mock_session,
        transaction_service=mock_tx_service,
        llm_client=mock_llm_client,
    )

    # Debe propagar InsufficientBalanceError
    with pytest.raises(InsufficientBalanceError) as exc_info:
        await chat_service.parse_expense(
            current_user=mock_user,
            text="Compré un reloj de 5000 dólares",
        )

    assert "Saldo insuficiente" in str(exc_info.value)