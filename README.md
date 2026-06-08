# FastAPI Template

A production-ready FastAPI template implementing Domain-Driven Design (DDD) and Clean Architecture principles with Dependency Injection, featuring authentication, database migrations, and Docker deployment.

## 🚀 Features

- **Clean Architecture**: Organized by contexts following DDD principles (NOT strict DDD)
- **Dependency Injection**: Using `dependency-injector` for better testability and modularity
- **Authentication**: API Key middleware with SHA-256 hashing (keys never stored in plain text)
- **REST API**: User management endpoints (`/api/v1/auth/users`) with cursor-based pagination
- **CLI Commands**: Typer-based administrative CLI for user and API key management
- **Domain Events**: Synchronous in-process event bus with subscriber pattern
- **Rate Limiting**: Sliding window rate limiter middleware (per-IP, configurable)
- **Distributed Cache**: Redis-backed cache (`RedisCacheClient`) with graceful degradation; `InMemoryCacheClient` used as the test double
- **Deep Health Check**: `/health` endpoint verifies database and Redis connectivity with latency reporting
- **Database Management**:
  - PostgreSQL 18 with async SQLAlchemy
  - Alembic for database migrations
  - Connection pooling and health checks
- **Docker Support**: Complete Docker Compose setup for development and production
- **Code Quality**:
  - Ruff for linting and formatting (configured with extensive rule sets)
  - Pre-commit hooks
  - Type hints targeting Python 3.14
- **Structured Logging**: Loguru-based wide events — one canonical, queryable log line per request with request-id correlation (JSON in production)
- **Settings Management**: Pydantic Settings with environment-based configuration
- **Production Ready**:
  - Multi-stage Docker builds
  - Non-root user execution
  - Hot reload in development

## 📋 Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer (used locally and in Docker)
- Docker & Docker Compose (for containerized deployment)
- PostgreSQL 18+ (handled by Docker Compose)
- Redis 8+ (handled by Docker Compose)

## 🏗️ Project Structure

```
fastapi-template/
├── src/
│   ├── main.py                    # FastAPI application entry point
│   ├── settings.py                # Application settings & configuration
│   ├── container.py               # Dependency injection container
│   └── contexts/                  # DDD contexts
│       ├── auth/                  # Authentication context
│       │   ├── domain/           # Domain models & repositories
│       │   ├── application/      # Use cases
│       │   └── infrastructure/   # Persistence, HTTP middleware, CLI
│       └── shared/               # Shared kernel
│           ├── domain/
│           └── infrastructure/   # Database, cache, logging
├── migrations/                    # Alembic database migrations
├── scripts/                       # Utility scripts (init_db, etc.)
├── secrets/                       # Environment variables (.env)
├── docker-compose.yaml           # Docker services definition
├── Dockerfile                    # Multi-stage Docker build
├── tests/                        # Test suite
│   ├── support/                 # Shared fixtures (DB, containers, factories)
│   └── contexts/                # Tests per bounded context (unit, integration, e2e)
├── Makefile                      # Development commands
└── pyproject.toml               # Project dependencies & config
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/p0llopez/fastapi-template.git
cd fastapi-template
```

### 2. Set Up Environment Variables

Create a `.env` file in the `secrets/` directory (used by the app and Docker Compose):

```bash
cp secrets/.env.example secrets/.env
```

### 3. Start with Docker Compose (Recommended)

```bash
# Build and start all services
make build && make start

# Or manually:
docker compose up --build
```

The API will be available at `http://localhost:8080`

### 4. Local Development (without Docker)

```bash
# Install dependencies with uv
make install

# Or manually:
uv sync

# Run database migrations (requires DATABASE_URL)
make migration-upgrade

# Start the application
uv run uvicorn src.main:app --reload
```

## 🛠️ Development Commands

The project includes a comprehensive Makefile for common tasks:

### Docker Operations

```bash
make start           # Start all services
make stop            # Stop all services
make build           # Build Docker images
make restart         # Restart all services
make logs            # Follow application logs
make shell           # Open bash in app container
make db-shell        # Open psql in database container
```

If your environment file lives in `secrets/.env`, run:

```bash
ENV_FILE=secrets/.env make db-shell
```

### Database Migrations

```bash
make migration-create              # Create auto-generated migration
make migration-create-empty        # Create empty migration template
make migration-upgrade             # Apply all pending migrations
make migration-downgrade           # Rollback last migration
make migration-history             # Show migration history
make migration-current             # Show current migration version
make migration-show                # Show current head revision
make migration-sql                 # Generate SQL for upgrade head
```

### Testing

```bash
make test                # Run all tests (Docker)
make test-unit           # Run unit tests (Docker)
make test-unit-local     # Run unit tests locally (fast, no Docker)
make test-integration    # Run integration tests (Docker, requires DB)
make test-e2e            # Run e2e tests (Docker, requires DB)
make test-cov            # Run tests with coverage (Docker)
```

### Code Quality

```bash
make fmt             # Format code with ruff
make lint            # Run linter with auto-fix
make all             # Run install, format, lint, and test
make clean           # Remove __pycache__ and .pyc files
```

### CLI Commands

```bash
# Make sure services are running first
make start

# Show CLI help
make cli

# Run CLI commands (pass args explicitly):
make cli args="auth list-users"
make cli args="auth create-user --username admin --email admin@example.com"
make cli args="auth create-api-key --user-id <uuid>"
make cli args="auth deactivate-api-key --user-id <uuid> --api-key <key>"

# For local development (without Docker):
uv run cli auth create-user --username admin --email admin@example.com
uv run cli auth list-users
```

## 📚 Architecture Overview

### Domain-Driven Design (DDD)

The project is organized into **contexts** (bounded contexts in DDD terminology):

- **Auth Context**: Handles authentication, users, and API keys
- **Shared Context**: Common infrastructure (database, logging, caching)

Each context follows a layered architecture:

1. **Domain Layer**: Business logic, entities, and repository interfaces
1. **Application Layer**: Use cases and business workflows
1. **Infrastructure Layer**: Database models, external services, and implementations

### Dependency Injection

The application uses `dependency-injector` for managing dependencies:

- `ApplicationContainer`: Root container
- Context-specific containers (e.g., `AuthContainer`, `SharedContainer`)
- Providers for repositories, use cases, and services

### Example: Adding a New Feature

To add a new feature (e.g., a "Products" context):

1. Create the context structure:

   ```
   src/contexts/products/
   ├── domain/
   │   ├── aggregates.py      # Product entity
   │   └── repositories.py    # Repository interface
   ├── application/
   │   └── use_cases/         # Business logic
   └── infrastructure/
       ├── container.py       # DI container
       └── persistence/       # Database models
   ```

1. Register in the main container (`src/container.py`)

1. Create database models and migrations

1. Implement use cases and endpoints

## 🔐 Authentication & Users

The template includes an API Key authentication system and user management:

- **User Management**: Create and manage users via REST API or CLI (passwords are bcrypt-hashed)
- **API Keys**: SHA-256 hashed — plain key shown only once at creation, never stored
- **HTTP**: All routes require `X-API-Key` header unless explicitly marked `@public`

### REST API Endpoints

| Method   | Route                     | Public | Description                    |
| -------- | ------------------------- | ------ | ------------------------------ |
| `POST`   | `/api/v1/auth/users`      | Yes    | Create user                    |
| `GET`    | `/api/v1/auth/users`      | No     | List users (cursor-paginated)  |
| `GET`    | `/api/v1/auth/users/{id}` | No     | Get user by ID                 |
| `DELETE` | `/api/v1/auth/users/{id}` | No     | Delete user                    |
| `GET`    | `/health`                 | Yes    | Deep health check (DB + Redis) |

### CLI Commands (API Key Management)

API key management is CLI-only for security:

```bash
make cli args="auth create-user"
make cli args="auth list-users"
make cli args="auth create-api-key --user-id <uuid>"
make cli args="auth deactivate-api-key --user-id <uuid> --api-key <key>"
```

### Authentication Behavior

- Global dependency: all routes require the `X-API-Key` header.
- Public routes: decorate handlers with `@public` to bypass auth.
- `POST /api/v1/auth/users` is public (needed to create the first user).
- `GET /health` is public (needed for load balancers/orchestrators).

````

## 🗄️ Database

### Migrations

The project uses Alembic for database migrations:

```bash
# Create a new migration after modifying models
make migration-create

# Apply migrations
make migration-upgrade

# Rollback last migration
make migration-downgrade
````

### Database Initialization

Run the initialization script to set up the database and apply migrations:

```bash
docker compose exec app python -m scripts.init_db
```

## 🐳 Docker Deployment

### Multi-Stage Build

The Dockerfile uses a multi-stage build for optimized images:

1. **Base**: Python 3.14 slim image
1. **Builder**: Installs dependencies using uv
1. **Runner**: Final image with only runtime dependencies

### Production Considerations

- Non-root user execution for security
- Compiled bytecode for faster startup
- Health checks for container orchestration
- Volume mounts for hot reload in development

### Environment Variables

Control build behavior:

```bash
# Build with dev dependencies
docker compose build --build-arg INSTALL_DEV=true

# Production build
docker compose build --build-arg INSTALL_DEV=false
```

## ⚙️ Configuration

Configuration is managed through `src/settings.py` using Pydantic Settings:

```python
from src.settings import settings

# Access configuration
if settings.is_production:
    # Production-specific code
    pass

# Database URL
db_url = settings.database_url

# Feature flags
log_level = settings.log_level
```

### Available Settings

- **Application**: `environment`, `log_level`, `log_format` (`console` | `json`, default `console`; set `json` in staging/production for structured wide-event logs)
- **Security**: `secret_key`, `allowed_origins`
- **Rate Limiting**: `rate_limit_requests` (default: 100), `rate_limit_window_seconds` (default: 60), `rate_limit_exclude_paths` (default: `["/health"]`)
- **Database**: `database_url`
- **Redis**: `redis_url` (default: `redis://localhost:6379/0`)

## 📝 Logging

The template uses **structured logging** (Loguru) built around **wide events**: every HTTP request emits **one canonical log line** carrying the full context of what happened — meant to be queried, not grepped.

### Output format

Controlled by `LOG_FORMAT` (env var / `settings.log_format`):

- `console` (default) — human-readable, colorized; for local development.
- `json` — one flat JSON object per line; for staging/production (set `LOG_FORMAT=json`).

`LOG_LEVEL` controls verbosity (default `INFO`). Outside development, Loguru's `diagnose` is disabled so tracebacks never leak local variable values.

### The canonical request line

The request middleware emits one line per request automatically — you wire nothing. Each event includes `request_id`, `method`, `path`, `route`, `status_code`, `duration_ms`, `outcome`, `client_ip`, `user_agent`, and (once authenticated) `user_id` and `api_key_id`. In development it also adds RAM deltas (`ram_start_mb`, `ram_end_mb`, `ram_delta_mb`). The level scales with the outcome: `5xx → ERROR`, `4xx → WARNING`, else `INFO`. The line is emitted even when the request raises.

Example (`LOG_FORMAT=json`):

```json
{"timestamp": "2026-06-06T14:41:57+02:00", "level": "INFO", "logger": "src.contexts.shared.infrastructure.logger.middleware", "message": "GET /api/v1/auth/users -> 200 (3.41ms)", "request_id": "0b9c1f2e-...", "method": "GET", "path": "/api/v1/auth/users", "route": "/api/v1/auth/users", "status_code": 200, "duration_ms": 3.41, "outcome": "ok", "client_ip": "127.0.0.1", "user_agent": "curl/8.4.0", "user_id": "a1b2...", "api_key_id": "c3d4..."}
```

### Request correlation (free)

Any `logger.*` call made while handling a request automatically inherits that request's context (`request_id`, identity) — no plumbing needed, including in the domain/application layers:

```python
from loguru import logger

logger.info("charge captured")  # emitted with request_id + user_id already attached
```

The request id is read from an inbound `X-Request-ID` header (or generated if absent) and echoed back in the response `X-Request-ID` header, so you can correlate client, logs, and downstream services.

### Adding your own high-cardinality context

To enrich the wide event with extra fields, call `bind_context(...)`. It lives in the **infrastructure layer**, so call it from infrastructure code (HTTP middleware, dependencies, event subscribers) — the same way the auth dependency attaches `user_id`/`api_key_id`:

```python
from src.contexts.shared.infrastructure.logger import bind_context

bind_context(tenant_id=str(tenant_id), plan="premium")
```

Whatever you bind lands on the request's canonical line and on every log emitted afterwards in that request. **Never log secrets** — the raw `X-API-Key` is deliberately never bound or stored; only `user_id`/`api_key_id` are.

## 🤖 AI Agent Configuration

The project ships a committed agent configuration so every clone inherits it:

- **`AGENTS.md`** — canonical instructions, read by all AI coding agents. `CLAUDE.md` re-exports it for Claude Code (`@AGENTS.md`).
- **`.claude/rules/`** — path-scoped guidance (architecture, coding principles, naming, testing, migrations, git) that loads automatically when editing matching files.
- **`.claude/settings.json`** — shared permissions (denies destructive git ops and reading `secrets/.env`) plus hooks that auto-run `ruff` format + lint on edit. Machine-specific overrides go in the gitignored `.claude/settings.local.json`.
- **`.worktreeinclude`** — copies `secrets/` into new worktrees created with `claude --worktree <name>`.

## Roadmap

Planned improvements for future development:

- [ ] **JWT Authentication** — Token-based auth for user sessions alongside API keys
- [ ] **Prometheus Metrics** — `/metrics` endpoint for application observability
- [ ] **OpenTelemetry Tracing** — Distributed tracing for request flows
- [ ] **Distributed Rate Limiting** — Redis-backed rate limiter for multi-instance deployments
- [ ] **Event Persistence** — Event sourcing / domain event storage for audit trails
- [ ] **Roles & Permissions (RBAC)** — Role-based access control for fine-grained authorization

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Pol López Cano**

- Email: pol.lopez.cano@gmail.com
- GitHub: [@p0llopez](https://github.com/p0llopez)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Astral's uv for blazing-fast package management
- The Python community for amazing tools and libraries

______________________________________________________________________

**Happy Coding! 🎉**
