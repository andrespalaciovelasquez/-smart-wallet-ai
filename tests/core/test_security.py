"""Pruebas unitarias para la capa de seguridad (Argon2id y JWT)"""

from datetime import timedelta
from backend.core.security import create_access_token, decode_access_token, get_password_hash, verify_password


def test_password_hashing_and_verification():
    """Valida el hashing de contraseñas con Argon2id"""
    password = "SuperPasswordSeguro123!"
    hashed = get_password_hash(password)

    # El hash no debe ser igual al texto plano
    assert hashed != password
    # La verificación con la clave correcta debe ser True
    assert verify_password(password, hashed) is True
    # Con clave incorrecta debe ser False
    assert verify_password("ClaveEquivocada", hashed) is False


def test_create_and_decode_access_token():
    """Valida la generación y decodificación de tokens JWT"""
    user_id = 42
    token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(minutes=15),
    )

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert "exp" in payload


def test_decode_invalid_jwt_returns_none():
    """Valida que un token corrupto o con firma inválida retorne None sin romper la app"""
    invalid_token = "token.totalmente.invalido"
    assert decode_access_token(invalid_token) is None