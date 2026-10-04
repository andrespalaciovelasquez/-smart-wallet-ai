# 💳 SmartWallet AI

> 📚 **Proyecto de Estudio y Portfolio Técnico**  
> Backend API para una Billetera Digital con Asistente Financiero IA.  
> Construido con **FastAPI**, **Clean Architecture / DDD** y patrones reales de **AI Engineering** (Structured Outputs, Búsqueda Semántica con **pgvector** y Prompts Compositivos desacoplados de cualquier proveedor LLM).

---

## 🎯 Motivación y Objetivos Técnicos

Este proyecto es un **ejercicio de construcción personal** para consolidar y demostrar competencias técnicas en dos áreas concretas:

### 1. Ingeniería de Backend (FastAPI + Python)
- Organización de código con **Modular Monolith / Clean Architecture**: dominios desacoplados con responsabilidad única en modelos ORM, esquemas de validación, repositorios, servicios y rutas.
- **Transacciones ACID** en operaciones monetarias: bloqueo a nivel de fila en PostgreSQL para garantizar que una transferencia entre dos usuarios sea atómica, consistente y sin condición de carrera.
- Manejo desacoplado de **excepciones de dominio** (ej. `InsufficientBalanceError`) y su traducción a respuestas HTTP estandarizadas.
- Validación estricta de esquemas de entrada/salida con **Pydantic v2**.

### 2. AI Engineering (LLMs Agnósticos + pgvector)
- **Structured Outputs deterministas**: extracción confiable de entidades financieras (monto, categoría, comercio) a partir de lenguaje natural mediante esquemas tipados Pydantic, desacoplado de la API o proveedor de LLM específico.
- **Almacenamiento vectorial híbrido**: registro de gastos con su embedding semántico en **PostgreSQL + `pgvector`**, habilitando búsquedas por significado (*"¿Cuánto gasté en salud?"* encuentra "Farmacia San Pablo" sin depender de coincidencia exacta de texto).
- **Arquitectura de Prompts Compositivos**: ensamblaje dinámico y modular de contexto (instrucciones de sistema + datos financieros reales + consulta del usuario) para garantizar respuestas verídicas (*grounding*) y evitar alucinaciones.
- **Testing desacoplado de LLMs con mocks**: suite de pruebas unitarias que simulan las respuestas del modelo de lenguaje, asegurando tests rápidos, deterministas y sin consumo de APIs externas.

---

## 📌 ¿Qué hace la aplicación?

**SmartWallet AI** simula el backend de una fintech de billetera digital. El dominio financiero es el **pretexto**: el objetivo real es resolver problemas técnicos concretos y no triviales.

El sistema es deliberadamente **conciso**: cada módulo expone solo los endpoints necesarios para demostrar un patrón técnico específico, sin código repetitivo que sature a quien lo revisa.

---

## 🚀 Endpoints (Alcance Reducido y Preciso)

### `POST /users/register`
Registra un nuevo usuario con contraseña hasheada en `bcrypt` y le crea automáticamente una billetera con **$1,000.00 USD** de saldo inicial (para facilitar las pruebas sin requerir un endpoint de depósito adicional).

**Patrón demostrado:** Creación transaccional de dos entidades relacionadas (usuario + billetera) como una única unidad de trabajo.

---

### `POST /users/login`
Autentica al usuario y retorna un **Bearer Token JWT** firmado con `HS256`.

**Patrón demostrado:** Autenticación stateless con JWT. Los endpoints protegidos validan este token.

---

### `POST /wallet/transfer`
Transfiere fondos entre dos usuarios de forma **atómica**. Si el emisor no tiene saldo suficiente o el receptor no existe, la operación se cancela sin modificar ningún balance. Registra dos movimientos contables inmutables (egreso para el emisor e ingreso para el receptor).

**Patrón demostrado:** Transacciones ACID con bloqueo de fila (`SELECT ... FOR UPDATE`), manejo de excepciones de negocio y ledger de doble entrada.

---

### `POST /chat/parse-expense`
El usuario envía texto libre: *"Ayer cené ramen con unos amigos por 38 dólares"*. El motor LLM extrae y valida determinísticamente `{monto: 38.00, moneda: USD, categoría: Restaurantes, descripción: "Cena ramen con amigos"}`. El egreso se descuenta de la billetera y se almacena junto a su **embedding semántico** en `pgvector`.

**Patrón demostrado:** Structured Outputs con esquemas Pydantic, consistencia transaccional y generación/indexación de embeddings vectoriales.

---

### `POST /chat/ask`
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
│   ├── security.py             # Hashing bcrypt y generación/validación de tokens JWT
│   ├── llm.py                  # Interfaz abstracta LLMClient + implementación Gemini (intercambiable)
│   └── prompts/                # 🧠 Motor de composición de prompts
│       ├── base.py             # Directrices del sistema y guardrails de seguridad
│       ├── registry.py         # Catálogo de plantillas desacopladas por caso de uso
│       └── builder.py          # Ensamblador modular (Sistema + Contexto Financiero + Consulta)
│
├── errors/                     # Manejo centralizado de errores
│   ├── exceptions.py           # Jerarquía de excepciones de negocio (ej. InsufficientBalanceError)
│   └── handlers.py             # Mapeo a respuestas HTTP estandarizadas (RFC 7807)
│
└── modules/                    # Dominios de negocio (Bounded Contexts)
    ├── users/
    │   ├── models.py           # Modelos ORM de SQLAlchemy (tablas users, wallets)
    │   ├── schemas.py          # Esquemas Pydantic de entrada/salida (DTOs)
    │   ├── repository.py       # Consultas y persistencia a nivel de base de datos
    │   ├── service.py          # Reglas de negocio: registro, hash y autenticación
    │   └── router.py           # Endpoints HTTP: /register, /login
    │
    ├── wallet/
    │   ├── models.py           # Modelo ORM de transacciones
    │   ├── schemas.py          # Esquemas Pydantic de transferencia
    │   ├── repository.py       # Consultas con bloqueo transaccional (SELECT FOR UPDATE)
    │   ├── service.py          # Lógica ACID y validaciones de saldo
    │   └── router.py           # Endpoint HTTP: /transfer
    │
    └── chat/
        ├── models.py           # Modelo ORM de gastos (con columna vector pgvector)
        ├── schemas.py          # Esquemas para Structured Outputs y consultas
        ├── repository.py       # Búsqueda por similitud vectorial (distancia coseno / L2)
        ├── service.py          # Orquestación: LLM → Embedding → BD → Prompt → Respuesta
        └── router.py           # Endpoints HTTP: /parse-expense, /ask

tests/                          # Suite de pruebas automatizadas
├── conftest.py                 # Fixtures compartidas (cliente de test async, mocks)
├── test_transfer_service.py    # Test unitario puro: validación de lógica ACID y saldos
└── test_expense_parser.py      # Test unitario: parsing de gastos usando mock del LLM
```

---

## 🛠️ Stack Tecnológico

| Área | Tecnología | Justificación |
|:---|:---|:---|
| **Framework Web** | FastAPI (Python 3.11+) | Rendimiento asíncrono y generación automática de OpenAPI |
| **Servidor ASGI** | FastAPI CLI (`fastapi dev`) / Uvicorn | Entorno de desarrollo moderno con recarga en caliente |
| **Validación y Schemas** | Pydantic v2 & Pydantic Settings | Tipado estricto y configuración validada |
| **Base de Datos** | PostgreSQL 16 + `pgvector` | Consistencia ACID relacional y búsqueda vectorial nativa |
| **ORM & Acceso a Datos** | SQLAlchemy 2.0 (`asyncpg`) | Mapeo objeto-relacional asíncrono moderno |
| **Modelos de IA (LLMs)** | Google Gemini (impl. por defecto) | Interfaz abstracta `LLMClient`: la lógica de negocio es agnóstica al proveedor; intercambiable por OpenAI, Anthropic, etc. |
| **Testing** | Pytest + `pytest-asyncio` + Mocks | Pruebas unitarias sin dependencias externas ni coste de API |
| **Gestor de Paquetes** | `uv` | Entorno virtual y resolución de dependencias de alta velocidad |
| **Contenedores** | Docker & Docker Compose | Aislamiento reproducible de PostgreSQL + `pgvector` |

---

## 🔄 Flujo de Uso Típico (User Journey)

```text
[POST /users/register]       → Crea usuario "Andrés" con billetera de $1,000.00 USD
             │
             ▼
[POST /users/login]          → Obtiene el JWT. Se autentica en Swagger UI (/docs)
             │
             ▼
[POST /wallet/transfer]      → Transfiere $50.00 a "María" de forma atómica (ACID)
                               Saldo de Andrés: $950.00 | Saldo de María: $1,050.00
             │
             ▼
[POST /chat/parse-expense]   → Andrés envía: "Gasté $35 en cenar ramen con amigos"
                               LLM extrae: {monto: 35, categoría: Restaurantes}
                               Egreso registrado + embedding guardado en pgvector
                               Saldo de Andrés: $915.00
             │
             ▼
[POST /chat/ask]             → Andrés pregunta: "¿Cuánto he gastado en comida?"
                               Búsqueda por similitud vectorial → localiza la cena de ramen
                               Inyecta saldo real ($915.00) en el prompt compositivo
                               LLM responde con datos exactos y verificables
```

---

## 🧪 Estrategia de Testing

Los tests demuestran **aislamiento de dependencias y pruebas de lógica crítica**:

- **`test_transfer_service.py`**: Test unitario de la lógica financiera. Verifica que se lance `InsufficientBalanceError` ante fondos insuficientes y que las transferencias exitosas calculen los saldos correctamente, utilizando mocks del repositorio sin tocar la base de datos real.
- **`test_expense_parser.py`**: Test de integración de IA con mock del cliente LLM. Valida que el pipeline de Structured Outputs procese e instancie el schema de Pydantic sin invocar llamadas externas ni generar costes.

---

## ⚙️ Instalación y Puesta en Marcha

### Prerrequisitos
- **Python 3.11+** y **[uv](https://docs.astral.sh/uv/)**.
- **Docker & Docker Compose** (para PostgreSQL con `pgvector`).
- API Key del proveedor LLM configurado (ej. Google Gemini u otro).

### Pasos
```bash
# 1. Clonar el repositorio
git clone https://github.com/andrespalaciovelasquez/-smart-wallet-ai
cd smart-wallet-ai

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Iniciar base de datos PostgreSQL + pgvector
docker compose up -d

# 4. Instalar dependencias del proyecto
uv sync

# 5. Ejecutar servidor en modo desarrollo
uv run fastapi dev backend/main.py
```

* **Swagger UI interactivo:** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`