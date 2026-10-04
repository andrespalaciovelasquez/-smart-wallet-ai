from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Esquemas de Entrada (Request)
class UserRegister(BaseModel):
    """Datos necesarios para registrar una nueva cuenta"""
    email: EmailStr = Field(
        description="Correo electrónico único del usuario",
        examples=["andres@example.com"]
    )
    full_name: str = Field(
        min_length=2,
        max_length=255,
        description="Nombre completo del usuario",
        examples=["Andrés Palacio"]
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Contraseña segura del usuario",
        examples=["ClaveSegura123!"]
    )

class UserLogin(BaseModel):
    """Credenciales para iniciar sesión"""
    email: EmailStr = Field(examples=["andres@example.com"])
    password: str = Field(examples=["ClaveSegura123!"])

# Esquemas de Salida (Responses)
class TokenResponse(BaseModel):
    """Token JWT entregado tras autenticación exitosa"""
    access_token: str = Field(
        description="Token JWT para acceder a endpoints protegidos",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token",
        examples=["bearer"]
    )

class UserResponse(BaseModel):
    """Datos públicos del usuario devueltos por la API"""
    id: int = Field(description="Identificador único del usuario", examples=[1])
    email: EmailStr = Field(description="Correo electrónico del usuario", examples=["andres@example.com"])
    full_name: str = Field(description="Nombre completo del usuario", examples=["Andrés Palacio"])
    created_at: datetime = Field(description="Fecha de registro", examples=["2026-10-04T15:00:00Z"])

    #Permite mapear directamente objetos User de SQLAlchemy a este Schema
    model_config = ConfigDict(from_attributes=True)