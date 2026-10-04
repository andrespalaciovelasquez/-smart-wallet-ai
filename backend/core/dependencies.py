from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import decode_access_token
from backend.errors.exceptions import UnauthorizedError
from backend.modules.users.models import User
from backend.modules.users.repository import UserRepository

# Configura el esquema Bearer estándar en Swagger y OpenAPI
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Extrae y valida el JWT Bearer token, devolviendo la entidad User autenticada."""
    token = credentials.credentials  # Extrae la cadena del token sin el prefijo "Bearer "
    payload = decode_access_token(token)

    if payload is None:
        raise UnauthorizedError("Token inválido o expirado")

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Token no contiene un identificador de usuario válido")

    user_id = int(user_id_str)
    user = await UserRepository(session).get_by_id(user_id)

    if user is None:
        raise UnauthorizedError("Usuario asociado al token no existe")

    return user