from typing import TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types
from backend.core.config import settings

# Tipo genérico para culquier esquema de Pydantic
T = TypeVar ("T", bound=BaseModel)

class LLMClient:
    """Cliente asíncrono para interactuar con modelos de lenguaje (LLMs)"""

    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.LLM_API_KEY)
        self.default_model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
    
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Genera respuestas de texto libre"""
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction if system_instruction else None,
        )
        response = await self.client.aio.models.generate_content(
            model=self.default_model,
            contents=prompt,
            config=config,
        )
        return response.text or ""
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
    ) -> T:
        """Extrae datos del LLM garantizando que cumplan un esquema Pydantic (Structured Output)"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction if system_instruction else None,
        )
        response = await self.client.aio.models.generate_content(
            model=self.default_model,
            contents=prompt,
            config=config,
        )
        return response.parsed
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Genera el vector de embeddings para un texto"""
        config = types.EmbedContentConfig(
            output_dimensionality=self.embedding_dimension
        )
        response = await self.client.aio.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=config,
        )
        return response.embeddings[0].values

# Instancia única para inyección de dependencias
llm_client = LLMClient()