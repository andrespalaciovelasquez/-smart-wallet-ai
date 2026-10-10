"""Pruebas unitarias para el registro y autenticación de usuarios (UserService)"""

import pytest
from pytest_mock import MockerFixture
from backend.errors.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from backend.modules.users.models import User
from backend.modules.users.schemas import UserLogin, UserRegister
from backend.modules.users.services import UserService


async def test_register_user_creates_wallet_atomically(mocker: MockerFixture):
    """Valida que el registro cree al usuario y su billetera inicial en un commit atómico"""
    mock_session = mocker.AsyncMock()
    mock_session.add = mocker.MagicMock()
    mock_user_repo = mocker.AsyncMock()
    # No existe usuario previo con este email
    mock_user_repo.get_by_email.return_value = None

    def fake_create(user: User):
        user.id = 1
        return user

    mock_user_repo.create.side_effect = fake_create

    service = UserService(session=mock_session, user_repo=mock_user_repo)

    data = UserRegister(
        email="nuevo@smartwallet.ai",
        full_name="Nuevo Usuario",
        password="Password123!",
    )

    created_user = await service.register_user(data)

    assert created_user.id == 1
    assert created_user.email == "nuevo@smartwallet.ai"
    # La contraseña debe haberse hasheado, no guardarse plana
    assert created_user.hashed_password != "Password123!"

    # Debe agregarse la billetera a la sesión y hacer commit
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


async def test_register_duplicate_email_raises_error(
    mock_user: User, mocker: MockerFixture
):
    """Valida que no se permita registrar un email duplicado"""
    mock_session = mocker.AsyncMock()
    mock_user_repo = mocker.AsyncMock()
    # Simular que el usuario ya existe
    mock_user_repo.get_by_email.return_value = mock_user

    service = UserService(session=mock_session, user_repo=mock_user_repo)

    data = UserRegister(
        email=mock_user.email,
        full_name="Duplicado",
        password="Password123!",
    )

    with pytest.raises(UserAlreadyExistsError) as exc_info:
        await service.register_user(data)

    assert "ya está registrado" in str(exc_info.value)
    mock_session.commit.assert_not_awaited()


async def test_authenticate_user_success(mocker: MockerFixture):
    """Valida que un login exitoso retorne un Bearer token JWT"""
    from backend.core.security import get_password_hash

    mock_session = mocker.AsyncMock()
    mock_user_repo = mocker.AsyncMock()

    real_hash = get_password_hash("PasswordCorrecto123!")
    user_in_db = User(
        id=7,
        email="andres@smartwallet.ai",
        full_name="Andrés",
        hashed_password=real_hash,
    )
    mock_user_repo.get_by_email.return_value = user_in_db

    service = UserService(session=mock_session, user_repo=mock_user_repo)

    login_data = UserLogin(
        email="andres@smartwallet.ai",
        password="PasswordCorrecto123!",
    )

    token_resp = await service.authenticate_user(login_data)

    assert token_resp.token_type == "bearer"
    assert token_resp.access_token is not None


async def test_authenticate_user_invalid_password_raises_error(mocker: MockerFixture):
    """Valida el rechazo de credenciales con contraseña equivocada"""
    from backend.core.security import get_password_hash

    mock_session = mocker.AsyncMock()
    mock_user_repo = mocker.AsyncMock()

    user_in_db = User(
        id=7,
        email="andres@smartwallet.ai",
        full_name="Andrés",
        hashed_password=get_password_hash("ClaveReal123!"),
    )
    mock_user_repo.get_by_email.return_value = user_in_db

    service = UserService(session=mock_session, user_repo=mock_user_repo)

    login_data = UserLogin(
        email="andres@smartwallet.ai",
        password="ClaveIncorrecta!",
    )

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate_user(login_data)