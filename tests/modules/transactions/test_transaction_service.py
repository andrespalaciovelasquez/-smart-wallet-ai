"""Pruebas unitarias para las reglas de negocio financieras (TransactionService)"""

from decimal import Decimal
import pytest
from pytest_mock import MockerFixture
from backend.errors.exceptions import InsufficientBalanceError
from backend.modules.transactions.models import Transaction, TransactionType
from backend.modules.transactions.schemas import TransactionCreate
from backend.modules.transactions.services import TransactionService
from backend.modules.users.models import User
from backend.modules.wallet.models import Wallet


async def test_create_expense_success(
    mock_user: User, mock_wallet: Wallet, mocker: MockerFixture
):
    """Valida el débito correcto del saldo al registrar un gasto válido"""
    # Arrange: Mocks con pytest-mock
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = mock_wallet

    mock_tx_repo = mocker.AsyncMock()
    mock_tx_repo.create.side_effect = lambda tx: tx  # Retorna la entidad recibida

    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_embedding.return_value = [0.1] * 768

    service = TransactionService(
        session=mock_session,
        transaction_repo=mock_tx_repo,
        wallet_repo=mock_wallet_repo,
        llm_client=mock_llm_client,
    )

    data = TransactionCreate(
        amount=Decimal("150.00"),
        type=TransactionType.EXPENSE,
        category="Servicios",
        description="Pago de electricidad",
    )

    # Act
    tx = await service.create_transaction(current_user=mock_user, data=data)

    # Assert: 1000.00 - 150.00 = 850.00
    assert mock_wallet.balance == Decimal("850.00")
    assert tx.amount == Decimal("150.00")
    assert tx.type == TransactionType.EXPENSE
    assert tx.embedding == [0.1] * 768

    # Commit atómico
    mock_session.commit.assert_awaited_once()


async def test_create_expense_insufficient_balance_raises_error(
    mock_user: User, mock_wallet: Wallet, mocker: MockerFixture
):
    """Valida que se impida registrar un gasto mayor al saldo disponible"""
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = mock_wallet

    service = TransactionService(
        session=mock_session,
        wallet_repo=mock_wallet_repo,
    )

    data = TransactionCreate(
        amount=Decimal("1500.00"),  # Saldo disponible es 1000.00
        type=TransactionType.EXPENSE,
        category="Compras",
        description="Laptop nueva",
    )

    with pytest.raises(InsufficientBalanceError) as exc_info:
        await service.create_transaction(current_user=mock_user, data=data)

    assert "Saldo insuficiente" in str(exc_info.value)
    # El saldo no debe haber cambiado
    assert mock_wallet.balance == Decimal("1000.00")
    # No debe haberse ejecutado commit
    mock_session.commit.assert_not_awaited()


async def test_create_income_increases_balance(
    mock_user: User, mock_wallet: Wallet, mocker: MockerFixture
):
    """Valida el incremento de saldo al registrar un ingreso"""
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = mock_wallet

    mock_tx_repo = mocker.AsyncMock()
    mock_tx_repo.create.side_effect = lambda tx: tx

    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_embedding.return_value = [0.2] * 768

    service = TransactionService(
        session=mock_session,
        transaction_repo=mock_tx_repo,
        wallet_repo=mock_wallet_repo,
        llm_client=mock_llm_client,
    )

    data = TransactionCreate(
        amount=Decimal("500.00"),
        type=TransactionType.INCOME,
        category="Salario",
        description="Pago quincenal",
    )

    tx = await service.create_transaction(current_user=mock_user, data=data)

    # 1000.00 + 500.00 = 1500.00
    assert mock_wallet.balance == Decimal("1500.00")
    assert tx.amount == Decimal("500.00")
    mock_session.commit.assert_awaited_once()


async def test_create_transaction_resilient_to_llm_embedding_failure(
    mock_user: User, mock_wallet: Wallet, mocker: MockerFixture
):
    """Valida que ante fallo de la API del LLM, la transacción financiera se guarde con embedding=None"""
    mock_session = mocker.AsyncMock()
    mock_wallet_repo = mocker.AsyncMock()
    mock_wallet_repo.get_by_user_id.return_value = mock_wallet

    mock_tx_repo = mocker.AsyncMock()
    mock_tx_repo.create.side_effect = lambda tx: tx

    # Simular fallo en la API del LLM (ej. rate limit 429)
    mock_llm_client = mocker.AsyncMock()
    mock_llm_client.generate_embedding.side_effect = RuntimeError("OpenAI rate limit")

    service = TransactionService(
        session=mock_session,
        transaction_repo=mock_tx_repo,
        wallet_repo=mock_wallet_repo,
        llm_client=mock_llm_client,
    )

    data = TransactionCreate(
        amount=Decimal("50.00"),
        type=TransactionType.EXPENSE,
        category="Alimentación",
        description="Almuerzo de trabajo",
    )

    # Debe completarse la operación financiera sin romperse
    tx = await service.create_transaction(current_user=mock_user, data=data)

    assert mock_wallet.balance == Decimal("950.00")
    assert tx.embedding is None  # Resiliente: se guardó sin vector
    mock_session.commit.assert_awaited_once()