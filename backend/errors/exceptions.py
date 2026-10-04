class DomainError(Exception):
    """Clase base para todos los errores de lógica de negocio del sistema"""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

class UserAlreadyExistsError(DomainError):
    """Se lanza cuando un correo ya está registrado en el sistema."""
    pass

class InvalidCredentialsError(DomainError):
    """Se lanza cuando el correo o la contraseña son incorrectos."""
    pass

class UserNotFoundError(DomainError):
    """Se lanza cuando un usuario no se encuentra en el sistema."""
    pass