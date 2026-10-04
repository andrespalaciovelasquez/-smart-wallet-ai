from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.security import get_password_hash, verify_password, create_access_token
from backend.errors.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from backend.modules.users.models import User
from backend.modules.users.schemas import UserRegister, UserLogin, TokenResponse
from backend.modules.users.repository import UserRepository
from backend.modules.wallet.models import Wallet

class UserService:
    """Orquesta la lógica de negocio para usuarios y su billetera inicial"""

    def __init__(self, session: AsyncSession, user_repo: UserRepository | None = None) -> None:
        self.session = session
        self.user_repo = user_repo or UserRepository(session)
    
    async def register_user(self, data: UserRegister) -> User:
        """Registra un nuevo usuario y crea su billetera inicial"""
        
        # Validar que el correo no este registrado
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise UserAlreadyExistsError(f"El correo {data.email} ya está registrado.")
        
        # Generar hash de la contraseña
        hashed_password = get_password_hash(data.password)

        # Persistir temporalmente el usuario (flush) para obtener su ID autoincremental
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hashed_password
        )
        user = await self.user_repo.create(user)

        # Crear billetera inicial (asociada al user.id generado por flush en el repo)
        wallet = Wallet(
            user_id=user.id,
            balance=Decimal("1000.00"),
            currency="USD"
        )
        self.session.add(wallet)

        # Commit atómico (se guardan User + Wallet juntos)
        await self.session.commit()
        await self.session.refresh(user)

        return user
        
    async def authenticate_user(self, data: UserLogin) -> TokenResponse:
        """Valida credenciales de acceso y retorna un Bearer Token JWT"""
        user = await self.user_repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError("Credenciales inválidas. Verifica tu correo o contraseña")
        
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        return TokenResponse(access_token=access_token, token_type="bearer")