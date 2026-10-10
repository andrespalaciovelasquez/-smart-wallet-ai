# 💳 SmartWallet AI

> 📚 **Proyecto de Estudio y Portfolio Técnico**  
> Backend API para una Billetera Digital con Asistente Financiero IA.  
> Construido con **FastAPI**, **Clean Architecture / DDD** y patrones reales de **AI Engineering** (Structured Outputs con OpenAI SDK, Búsqueda Semántica con **pgvector**, Embeddings Matryoshka y Prompts Compositivos desacoplados de cualquier proveedor LLM).

---

## 🎯 Motivación y Objetivos Técnicos

Este proyecto es un **ejercicio de construcción personal** para consolidar y demostrar competencias técnicas en dos áreas concretas:

### 1. Ingeniería de Backend (FastAPI + Python)
- Organización de código con **Modular Monolith / Clean Architecture**: dominios desacoplados con responsabilidad única en modelos ORM, esquemas de validación, repositorios, servicios y rutas.
- **Transacciones atómicas** en operaciones monetarias: creación de transacciones y actualización de saldo de billetera en un único `commit`, garantizando consistencia de datos.
- Manejo desacoplado de **excepciones de dominio** (ej. `InsufficientBalanceError`, `UnauthorizedError`) y su traducción centralizada a respuestas HTTP estandarizadas.
- Validación estricta de esquemas de entrada/salida con **Pydantic v2**.
- Autenticación **stateless** con JWT (HS256) y **Argon2id** (OWASP 2026) para hashing de contraseñas.

### 2. AI Engineering (Protocolo Estándar OpenAI + pgvector)
- **Protocolo Estándar de la Industria & Cero Vendor Lock-in**: Implementación basada en el SDK oficial de OpenAI (`openai.AsyncOpenAI`) utilizando el patrón *OpenAI-compatible protocol*. A través de la variable `LLM_BASE_URL`, el sistema conmuta sin tocar una sola línea de código entre **Google Gemini** (desarrollo gratuito), **OpenAI / Azure OpenAI** (producción enterprise) o **modelos locales on-premise** como Ollama/vLLM.
- **Almacenamiento vectorial híbrido**: registro de transacciones financieras con su embedding semántico en **PostgreSQL + `pgvector`**, habilitando búsquedas por significado (*"¿Cuánto gasté en salud?"* encuentra "Farmacia San Pablo" sin depender de coincidencia exacta de texto).
- **Embeddings Matryoshka tipados**: generación de vectores fijados a 768 dimensiones estándar (`dimensions=768`) para maximizar velocidad de cómputo y ahorro de almacenamiento indexado.
- **Generación de embeddings resiliente**: si la API del LLM experimenta rate limits o indisponibilidad, la transacción financiera se procesa sin bloquear al usuario (el embedding queda en `NULL` para reintento asíncrono posterior).
- **Structured Outputs deterministas**: extracción estricta de entidades financieras a partir de lenguaje natural mediante `client.beta.chat.completions.parse` con esquemas Pydantic, garantizando outputs válidos sin parseos manuales propensos a fallos.
- **Arquitectura de Prompts Compositivos**: ensamblaje dinámico y modular de contexto (instrucciones de sistema + datos financieros reales + consulta del usuario) para garantizar respuestas verídicas (*grounding*) y mitigar alucinaciones.

---

## 📌 ¿Qué hace la aplicación?

**SmartWallet AI** simula el backend de una fintech de billetera digital. El dominio financiero es el **pretexto**: el objetivo real es resolver problemas técnicos concretos y no triviales.

El sistema es deliberadamente **conciso**: cada módulo expone solo los endpoints necesarios para demostrar un patrón técnico específico, sin código repetitivo que sature a quien lo revisa.

---

## 🚀 Endpoints

### `POST /users/register`
Registra un nuevo usuario con contraseña hasheada en **Argon2id** y le crea automáticamente una billetera con **$1,000.00 USD** de saldo inicial (para facilitar las pruebas sin requerir un endpoint de depósito adicional).

**Patrón demostrado:** Creación transaccional de dos entidades relacionadas (usuario + billetera) como una única unidad de trabajo atómica (`flush` + `commit`).

---

### `POST /users/login`
Autentica al usuario y retorna un **Bearer Token JWT** firmado con `HS256`.

**Patrón demostrado:** Autenticación stateless con JWT. Los endpoints protegidos validan este token mediante la dependencia `get_current_user` con esquema `HTTPBearer`.

---

### `GET /wallet/me` 🔒
Devuelve los datos y saldo actual de la billetera del usuario autenticado.

**Patrón demostrado:** Endpoint protegido con inyección de dependencia de autenticación (`Depends(get_current_user)`).

---

### `POST /transactions/` 🔒
Registra un movimiento financiero (`INCOME` o `EXPENSE`). Si es un gasto, valida que el usuario tenga saldo suficiente, descuenta el monto de la billetera y genera un **embedding semántico** del texto de la transacción con IA para futuras búsquedas por similitud.

**Patrón demostrado:** Commit atómico (saldo de wallet + transacción en una operación indivisible), validación de reglas de negocio (`InsufficientBalanceError`), generación de embeddings con LLM resiliente a fallos y almacenamiento vectorial en `pgvector`.

---

### `GET /transactions/` 🔒
Devuelve el historial de transacciones del usuario autenticado, ordenadas de la más reciente a la más antigua, con paginación básica (`limit`).

**Patrón demostrado:** Consultas paginadas con SQLAlchemy 2.0 async y serialización automática ORM → Pydantic via `from_attributes`.

---

### `POST /chat/parse-expense` 🔒
El usuario envía texto libre: *"Ayer cené ramen con unos amigos por 38 dólares"*. El motor LLM extrae y valida determinísticamente `{monto: 38.00, categoría: Restaurantes, descripción: "Cena ramen con amigos"}`. El egreso se descuenta de la billetera y se almacena junto a su embedding semántico.

**Patrón demostrado:** Structured Outputs con esquemas Pydantic, consistencia transaccional y generación/indexación de embeddings vectoriales.

---

### `POST /chat/ask` 🔒
El usuario pregunta en lenguaje natural: *"¿En qué cosas de salud gasté dinero este mes?"*. El sistema genera el vector de la consulta, realiza una **búsqueda por similitud semántica** (`pgvector`) contra los gastos históricos, recupera el saldo actual y ensambla un prompt compositivo para que el LLM responda con datos exactos y grounding real.

**Patrón demostrado:** Pipeline RAG (Retrieval-Augmented Generation) integrado con base de datos relacional y vectorial.

---

## 🏛️ Estructura del Código

```text
backend/
├── main.py                     # Instancia FastAPI, registro de routers y ciclo de vida (lifespan)
├── middleware.py               # Logging estructurado, tiempos de respuesta y CORS
│
├── core/                       # Infraestructura técnica transversal
│   ├── config.py               # Configuración tipada vía Pydantic Settings (.env)
│   ├── database.py             # Engine async de SQLAlchemy + sesión asyncpg + pgvector
│   ├── dependencies.py         # Dependencia get_current_user (HTTPBearer + JWT)
│   ├── security.py             # Hashing Argon2id (pwdlib) y generación/validación de tokens JWT
│   ├── llm.py                  # Cliente LLM agnóstico con SDK oficial OpenAI (compatible con Gemini, OpenAI, Ollama, etc.)
│   └── prompts.py              # 🛡️ Políticas corporativas globales de seguridad y guardrails para LLMs (SSOT)
│
├── errors/                     # Manejo centralizado de errores
│   ├── exceptions.py           # Jerarquía de excepciones de dominio (DomainError base)
│   └── handlers.py             # Mapeo centralizado excepción → código HTTP
│
└── modules/                    # Dominios de negocio (Bounded Contexts)
    ├── users/
    │   ├── models.py           # Modelo ORM: tabla users
    │   ├── schemas.py          # Esquemas Pydantic: UserRegister, UserLogin, TokenResponse, UserResponse
    │   ├── repository.py       # Consultas: get_by_email, get_by_id, create
    │   ├── services.py         # Reglas de negocio: registro atómico (user + wallet) y autenticación
    │   └── routes.py           # Endpoints HTTP: /register, /login
    │
    ├── wallet/
    │   ├── models.py           # Modelo ORM: tabla wallets (balance, currency, timestamps)
    │   ├── schemas.py          # Esquema Pydantic: WalletResponse
    │   ├── repository.py       # Consulta: get_by_user_id
    │   ├── services.py         # Lógica de negocio: consulta de billetera del usuario autenticado
    │   └── routes.py           # Endpoint HTTP protegido: GET /wallet/me
    │
    ├── transactions/
    │   ├── models.py           # Modelo ORM: tabla transactions (con columna Vector pgvector 768d)
    │   ├── schemas.py          # Esquemas: TransactionCreate (entrada validada) y TransactionResponse
    │   ├── repository.py       # Consultas: create (con flush), get_by_wallet_id, search_semantic (KNN pgvector)
    │   ├── services.py         # Lógica financiera: validación de saldo, commit atómico, embedding IA
    │   └── routes.py           # Endpoints HTTP protegidos: POST y GET /transactions/
    │
    └── chat/                   # 💬 Asistente Financiero & IA Conversacional
        ├── schemas.py          # Esquemas para Structured Outputs y consultas RAG
        ├── prompts.py          # 🧠 Prompts de dominio financiero y FinancialPromptBuilder (RAG)
        ├── services.py         # Orquestación: LLM → Embedding → pgvector → Prompt Compositivo → Respuesta
        └── routes.py           # Endpoints HTTP protegidos: /parse-expense, /ask
│
tests/                          # 🧪 Suite de pruebas automatizadas (Espejo de Dominios)
├── conftest.py                 # Fixtures compartidos globales (mock_user, mock_wallet)
├── core/
│   └── test_security.py        # Pruebas de hashing Argon2id y ciclo de vida JWT
└── modules/
    ├── users/
    │   └── test_auth_service.py # Registro atómico, detección de duplicados y login
    ├── transactions/
    │   └── test_transaction_service.py # Débito, saldo insuficiente y resiliencia de IA
    └── chat/
        ├── test_expense_parser.py # Extracción estructurada con Pydantic y OpenAI SDK
        └── test_financial_rag.py  # Pipeline RAG con pgvector, grounding y fallbacks
```

---

## 🛠️ Stack Tecnológico

| Área | Tecnología | Justificación |
|:---|:---|:---|
| **Framework Web** | FastAPI (Python 3.13+) | Rendimiento asíncrono y generación automática de OpenAPI |
| **Servidor ASGI** | FastAPI CLI (`fastapi dev`) / Uvicorn | Entorno de desarrollo moderno con recarga en caliente |
| **Testing & Mocking** | Pytest (`pytest-asyncio`, `pytest-mock`) | Suite en espejo de dominios (16 tests) con mocks asíncronos rápidos y sin costos de API |
| **Validación y Schemas** | Pydantic v2 & Pydantic Settings | Tipado estricto y configuración validada |
| **Base de Datos** | PostgreSQL 17 + `pgvector` | Consistencia ACID relacional y búsqueda vectorial nativa |
| **ORM & Acceso a Datos** | SQLAlchemy 2.0 (`asyncpg`) | Mapeo objeto-relacional asíncrono moderno (`Mapped` / `mapped_column`) |
| **Hashing de Contraseñas** | Argon2id (`pwdlib[argon2]`) | Ganador de PHC 2015 y recomendación OWASP 2026 |
| **Autenticación** | JWT (`pyjwt`) + `HTTPBearer` | Tokens stateless con esquema Bearer estándar |
| **Ecosistema de IA (LLMs)** | OpenAI SDK oficial (`openai` AsyncOpenAI) | Protocolo estándar de la industria. Provee interoperabilidad total con OpenAI, Azure OpenAI, Google Gemini (OpenAI compatibility endpoint), Ollama o vLLM simplemente ajustando `LLM_BASE_URL` sin tocar código de la aplicación. |
| **Gestor de Paquetes** | `uv` | Entorno virtual y resolución de dependencias de alta velocidad |
| **Contenedores** | Docker & Docker Compose | Aislamiento reproducible de PostgreSQL + `pgvector` |

---

### 🌐 Patrón de Interoperabilidad Multi-Proveedor (OpenAI Compatible Protocol)

En lugar de utilizar SDKs propietarios de cada fabricante (que generan vendor lock-in y obligan a reescribir código al migrar de proveedor), **SmartWallet AI** adopta el **protocolo OpenAI como estándar arquitectónico**.

Cualquier proveedor compatible se configura exclusivamente mediante variables de entorno:

| Entorno / Proveedor | `LLM_BASE_URL` | `LLM_MODEL` | `EMBEDDING_MODEL` | Beneficio |
|:---|:---|:---|:---|:---|
| **Desarrollo (Google Gemini)** | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-3.5-flash` | `gemini-embedding-001` | **Gratuito**: pruebas completas sin costos de tarjeta. |
| **Producción (OpenAI Nativo)** | *(vacío / omitido)* | `gpt-4o-mini` | `text-embedding-3-small` | Rendimiento oficial en la nube de OpenAI. |
| **Corporativo (Azure OpenAI)** | `https://{resource}.openai.azure.com/openai/deployments/{deploy}` | `gpt-4o` | `text-embedding-3-small` | Cumplimiento empresarial, SLA y aislamiento de red. |
| **Privado / Local (Ollama/vLLM)**| `http://localhost:11434/v1` | `llama3.1` | `nomic-embed-text` | 100% On-Premise y privacidad absoluta de datos. |

---

## 🔄 Flujo de Uso Típico (User Journey)

```text
[POST /users/register]       → Crea usuario "Andrés" con billetera de $1,000.00 USD
             │
             ▼
[POST /users/login]          → Obtiene el JWT. Se autentica en Swagger UI (/docs)
             │
             ▼
[GET /wallet/me]             → Consulta su saldo: $1,000.00 USD
             │
             ▼
[POST /transactions/]        → Registra gasto: "Cena en restaurante" $45.50
                               Saldo actualizado: $954.50
                               Embedding semántico generado y almacenado en pgvector
             │
             ▼
[GET /transactions/]         → Lista su historial de movimientos ordenado por fecha
             │
             ▼
[POST /chat/parse-expense]   → Andrés envía: "Gasté $35 en cenar ramen con amigos"
                                LLM extrae: {monto: 35, categoría: Restaurantes}
                               Egreso registrado + embedding guardado en pgvector
                               Saldo de Andrés: $919.50
             │
             ▼
[POST /chat/ask]             → Andrés pregunta: "¿Cuánto he gastado en comida?"
                                Búsqueda por similitud vectorial → localiza gastos de comida
                               Inyecta saldo real en el prompt compositivo
                               LLM responde con datos exactos y verificables
```

---

## ⚙️ Instalación y Puesta en Marcha

### Prerrequisitos
- **Python 3.13+** y **[uv](https://docs.astral.sh/uv/)**.
- **Docker & Docker Compose** (para PostgreSQL con `pgvector`).
- API Key del proveedor LLM configurado (ej. Google Gemini u otro).

### Pasos
```bash
# 1. Clonar el repositorio
git clone https://github.com/andrespalaciovelasquez/smart-wallet-ai
cd smart-wallet-ai

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Iniciar base de datos PostgreSQL + pgvector
docker compose up -d

# 4. Instalar dependencias del proyecto
uv sync

# 5. Ejecutar servidor en modo desarrollo
uv run fastapi dev backend/main.py

# 6. Ejecutar la suite completa de pruebas automatizadas (16 tests)
uv run pytest
```

* **Swagger UI interactivo:** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`