from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Variables de la App
    APP_ENV: str = "development"
    PROJECT_NAME: str = "SmartWallet AI"

    # Seguridad y Autenticación JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Base de Datos (PostgreSQL + pgvector)
    DATABASE_URL: str

    # Inteligencia Artificial (Agnóstico de Proveedor)
    LLM_API_KEY: str
    LLM_MODEL: str
    EMBEDDING_MODEL: str

    @property
    def is_debug(self) -> bool:
        return self.APP_ENV == "development"

    # Configuración para leer el archivo .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()  # Instanciamos las variables de entorno