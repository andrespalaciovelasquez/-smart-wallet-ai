"""Fixtures compartidos para la suite de pruebas unitarias"""

from decimal import Decimal
import pytest
from backend.modules.users.models import User
from backend.modules.wallet.models import Wallet


@pytest.fixture
def mock_user() -> User:
    """Fixture de usuario autenticado"""
    return User(
        id=1,
        email="andres@smartwallet.ai",
        full_name="Andrés Palacio",
        hashed_password="hashed_password_mock",
    )


@pytest.fixture
def mock_wallet(mock_user: User) -> Wallet:
    """Fixture de billetera con saldo inicial disponible"""
    return Wallet(
        id=1,
        user_id=mock_user.id,
        balance=Decimal("1000.00"),
        currency="USD",
    )