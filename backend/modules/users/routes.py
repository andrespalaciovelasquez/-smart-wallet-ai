from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.users.schemas import TokenResponse, UserLogin, UserRegister, UserResponse
from backend.modules.users.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Proveedor de dependencia para inyectar UserService en las rutas"""
    return UserService(session=db)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Crea la cuenta de usuario y le asigna automáticamente una billetera inicial con $1,000.00 USD"
)
async def register_user(
    data: UserRegister,
    service: UserService = Depends(get_user_service)
):
    user = await service.register_user(data)
    return user

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Valida las credenciales del usuario y emite un token de acceso JWT"
)
async def login_user(
    data: UserLogin,
    service: UserService = Depends(get_user_service)
):
    token_response = await service.authenticate_user(data)
    return token_response