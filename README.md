# ai-agent-platform

[![Python](https://img.shields.io/badge/python-3.13-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138+-0b6e3f?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An **AI agent chat platform** with voice input/output, built with FastAPI, async SQLAlchemy, and SQLite. Create custom AI agents, hold multi-turn conversations, and send voice messages that are transcribed, processed, and responded to with speech — all powered by OpenAI.

## Features

- **Agent management** — Create, update, and delete AI agents with custom system prompts.
- **Chat sessions** — Scoped conversations tied to an agent, with auto-titling.
- **Text messaging** — Send messages to an agent and receive AI-generated replies.
- **Voice messaging** — Upload audio (WAV, MP3, OGG, WebM) for STT transcription, AI completion, and TTS speech synthesis — the full pipeline in one request.
- **Audio file serving** — Generated speech files served at `/audio/{session_id}/{filename}`.
- **Health check** — `GET /health` endpoint with database reachability probe.
- **Structured error handling** — Consistent JSON error responses via a typed exception hierarchy.
- **JSON logging** — Structured request logging for observability.
- **Docker support** — One-command deployment with Docker Compose (backend + frontend).

## Architecture

The backend follows a **layered architecture**:

```
┌──────────────┐
│  Controllers │  ← FastAPI route handlers (input validation, response formatting)
├──────────────┤
│   Services   │  ← Business logic, orchestration, OpenAI integration
├──────────────┤
│ Repositories │  ← Data access layer (SQLAlchemy queries, flush-based)
├──────────────┤
│    Models    │  ← SQLAlchemy ORM models
└──────────────┘
```

- **Dependency injection** via FastAPI's `Depends` — sessions, clients, and services are wired automatically.
- **Transaction management** owned by the dependency layer — repositories use `flush`, the `get_db` dependency commits on success and rolls back on exception.
- **OpenAI client** injected as a typed `Depends`; raises `502 OpenAIException` if `OPENAI_API_KEY` is not configured.

## Tech Stack

| Category       | Technology                                                    |
| -------------- | ------------------------------------------------------------- |
| Runtime        | Python 3.13                                                   |
| Framework      | FastAPI (with `fastapi[standard]`)                            |
| Database       | SQLite via `aiosqlite` + async SQLAlchemy 2.0                 |
| Migrations     | Alembic (async)                                               |
| AI / Voice     | OpenAI API (GPT-4o-mini, Whisper, TTS)                        |
| Validation     | Pydantic (via pydantic-settings)                              |
| Testing        | pytest + pytest-asyncio + httpx (ASGI transport)              |
| Linting        | Ruff                                                          |
| Type checking  | `ty`                                                          |
| Container      | Docker + Docker Compose                                       |
| Frontend       | React 19, TypeScript 6, Vite 8, Tailwind CSS v4 *(separate)*  |

## Prerequisites

- Python **3.13** or later
- [uv](https://docs.astral.sh/uv/) (recommended) **or** pip
- An [OpenAI API key](https://platform.openai.com/api-keys) (required for voice and chat features)

## Getting Started

### 1. Clone the repository

```sh
git clone <repository-url>
cd ai-agent-platform
```

### 2. Environment configuration

Copy the example environment file and fill in your settings:

```sh
cp .env.example .env
```

At a minimum, set your OpenAI API key in `.env`:

```env
OPENAI_API_KEY=sk-...
```

The default `DATABASE_URL` uses a local SQLite file at `data/app.db`, which is automatically created.

### 3. Install dependencies

#### Recommended — with uv

```sh
uv sync
```

This creates a virtual environment at `.venv` and installs all runtime and dev dependencies.

#### Alternative — with pip

```sh
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # if available, or install dev deps manually
```

> **Note**: `requirements.txt` is auto-generated. For development, `uv sync` is preferred as it ensures lockfile consistency.

### 4. Run database migrations

```sh
uv run alembic upgrade head
```

### 5. Start the development server

```sh
uv run fastapi dev
```

The server starts at **http://localhost:8000** with hot-reload enabled. The API docs are available at **http://localhost:8000/docs**.

---

## Docker

For a full stack deployment (backend + frontend), including automated migrations:

```sh
docker compose up --build -d
```

- **Backend** — http://localhost:8000
- **Frontend** — http://localhost:8080

Stop and clean up:

```sh
docker compose down -v
```

View logs:

```sh
docker compose logs -f
```

> The backend runs as a non-root user (`appuser`, uid 999). SQLite data and audio files persist in a named Docker volume (`app_data`). The entrypoint runs `alembic upgrade head` automatically before starting the server.

---

## Project Structure

```
├── app/
│   ├── main.py                  # FastAPI application entrypoint
│   ├── core/
│   │   ├── app.py               # App factory (create_app)
│   │   ├── config.py            # Pydantic settings (reads .env)
│   │   ├── database.py          # Async engine, session factory, Base
│   │   ├── errors.py            # AppException hierarchy (404/400/409/502)
│   │   ├── openai.py            # OpenAI client dependency injection
│   │   ├── validators.py        # Audio file validation
│   │   ├── logger.py            # JSON logging configuration
│   │   └── logging_middleware.py# ASGI request logging middleware
│   ├── controllers/
│   │   ├── router.py            # API router (prefix /api/v1)
│   │   ├── agent.py             # Agent CRUD endpoints
│   │   ├── chat_session.py      # Session CRUD endpoints
│   │   ├── message.py           # Message endpoints + chat completion
│   │   └── voice.py             # Voice message pipeline (STT → chat → TTS)
│   ├── models/
│   │   ├── agent.py             # Agent ORM model
│   │   ├── chat_session.py      # ChatSession ORM model
│   │   ├── message.py           # Message ORM model (user/assistant roles)
│   │   └── audio_file.py        # AudioFile ORM model
│   ├── repositories/
│   │   ├── base.py              # Generic CRUD repository
│   │   ├── agent.py
│   │   ├── chat_session.py
│   │   ├── message.py
│   │   └── audio_file.py
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── chat_session.py
│   │   ├── message.py
│   │   ├── audio_file.py
│   │   └── error.py
│   └── services/
│       ├── agent.py
│       ├── chat_session.py
│       ├── message.py           # OpenAI chat completion logic
│       └── voice.py             # STT + TTS orchestration
├── alembic/                     # Database migrations (async)
│   └── versions/
├── tests/                       # Async pytest suite
│   ├── conftest.py              # Fixtures (in-memory SQLite, mock OpenAI)
│   ├── test_agents.py
│   ├── test_sessions.py
│   ├── test_messages.py
│   └── test_voice.py
├── data/
│   └── audio_files/             # Generated TTS audio storage
├── frontend/                    # React + TypeScript frontend (see frontend/README.md)
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
├── docker-compose.yml
├── Dockerfile
├── docker-entrypoint.sh
├── pyproject.toml
└── .env.example
```

## API Overview

All routes are mounted under the `/api/v1` prefix.

| Method | Endpoint                              | Description                    |
| ------ | ------------------------------------- | ------------------------------ |
| POST   | `/api/v1/agents/`                     | Create an agent                |
| GET    | `/api/v1/agents/`                     | List all agents                |
| GET    | `/api/v1/agents/{id}`                 | Get an agent by ID             |
| PUT    | `/api/v1/agents/{id}`                 | Update an agent                |
| DELETE | `/api/v1/agents/{id}`                 | Delete an agent                |
| POST   | `/api/v1/sessions/`                   | Create a chat session          |
| GET    | `/api/v1/sessions/agent/{agent_id}`   | List sessions for an agent     |
| GET    | `/api/v1/sessions/{id}`               | Get a session by ID            |
| DELETE | `/api/v1/sessions/{id}`               | Delete a session               |
| GET    | `/api/v1/sessions/{id}/messages/`     | List messages in a session     |
| POST   | `/api/v1/sessions/{id}/messages/`     | Send a text message            |
| POST   | `/api/v1/sessions/{id}/voice/`        | Send a voice message (upload)  |
| GET    | `/health`                             | Health check (with DB probe)   |

> Interactive API documentation is automatically available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Testing

The test suite uses an in-memory SQLite database with per-test table cleanup and a mocked OpenAI client.

```sh
uv run pytest
```

Run a specific test file:

```sh
uv run pytest tests/test_agents.py -v
```

Key fixtures:
- `client` — HTTP client backed by the real app (DB only).
- `client_with_openai` — HTTP client with a mocked OpenAI client — use for any endpoint that calls OpenAI.
- `mock_openai` — `AsyncMock`-based OpenAI stub.

## Development

### Linting and formatting

```sh
uv run ruff check --fix .
uv run ruff format .
```

### Type checking

```sh
uv run ty check .
```

### Pre-commit hooks

```sh
uv run pre-commit run --all-files
```

### Database migrations

```sh
uv run alembic revision --autogenerate -m "description of change"
uv run alembic upgrade head
```

### Adding dependencies

After modifying `pyproject.toml`:

```sh
uv lock
```

This updates `uv.lock` and `requirements.txt`. Both are checked into version control.

## Frontend

A React 19 + TypeScript + Vite frontend lives in the `frontend/` directory. It proxies API requests to the backend during development.

For frontend-specific setup instructions and documentation, see [`frontend/README.md`](frontend/README.md).

## Environment Variables

All configuration is managed via pydantic-settings and read from `.env`. The full set of variables is defined in `app/core/config.py`.

| Variable                  | Default                   | Description                              |
| ------------------------- | ------------------------- | ---------------------------------------- |
| `DATABASE_URL`            | `sqlite+aiosqlite:///./data/app.db` | Database connection string  |
| `OPENAI_API_KEY`          | —                         | OpenAI API key (optional, but needed for AI features) |
| `OPENAI_MODEL_NAME`       | `gpt-4o-mini`             | Chat model                               |
| `OPENAI_STT_MODEL`        | `whisper-1`               | Speech-to-text model                     |
| `OPENAI_TTS_MODEL`        | `tts-1`                   | Text-to-speech model                     |
| `OPENAI_TTS_VOICE`        | `alloy`                   | TTS voice                                |
| `OPENAI_TTS_OUTPUT_MIME`  | `audio/mpeg`              | TTS output MIME type                     |
| `AUDIO_STORAGE_DIR`       | `data/audio_files`        | Directory for audio file storage         |
| `MAX_AUDIO_FILE_SIZE`     | `10485760` (10 MB)        | Maximum upload size in bytes             |

## License

MIT
