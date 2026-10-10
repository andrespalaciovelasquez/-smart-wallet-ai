from typing import TypeVar
from pydantic import BaseModel
from openai import AsyncOpenAI
from backend.core.config import settings

# Tipo genérico para culquier esquema de Pydantic
T = TypeVar ("T", bound=BaseModel)

class LLMClient:
    """Cliente asíncrono para interactuar con modelos de lenguaje utilizando el estándar OpenAI"""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL    
        )
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
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content or ""
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
    ) -> T:
        """Extrae datos garantizando que cumplan un esquema Pydantic (Structured Outputs nativo de OpenAI)"""
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        # Utiliza la API beta de OpenAI para parseo determinista de Pydantic
        completion = await self.client.beta.chat.completions.parse(
            model=self.default_model,
            messages=messages,
            response_format=response_schema,
        )
        return completion.choices[0].message.parsed
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Genera el vector de embeddings para un texto usando el endpoint estándar /v1/embeddings"""
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
            dimensions=self.embedding_dimension
        )
        return response.data[0].embedding

# Instancia única para inyección de dependencias
llm_client = LLMClient()