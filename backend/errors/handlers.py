from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from backend.errors.exceptions import DomainError, InvalidCredentialsError, UserAlreadyExistsError, UserNotFoundError, UnauthorizedError, WalletNotFoundError, InsufficientBalanceError

async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Atrapa cualquier excepción de dominio y la traduce a su código HTTP correspondiente"""
    status_code = status.HTTP_400_BAD_REQUEST

    if isinstance(exc, (InvalidCredentialsError, UnauthorizedError)):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, (UserNotFoundError, WalletNotFoundError)):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, UserAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, InsufficientBalanceError):
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message}
    )

def register_exception_handlers(app: FastAPI) -> None:
    """Registra los exception handlers centralizados en la instancia de FastAPI"""
    app.add_exception_handler(DomainError, domain_exception_handler)