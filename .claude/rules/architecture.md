---
description: Hexagonal DDD architecture patterns, DI container, repository pattern, caching, and public route decorator
paths: ["src/contexts/**"]
---

# Architecture Patterns

## Hexagonal Layers

- **Domain** (`src/contexts/*/domain`): Pure Python, NO infrastructure or application deps. Entities extend `AggregateRoot` (Pydantic BaseModel at `src/contexts/shared/domain/aggregate_root.py`). IDs are `UUID`.
- **Application** (`src/contexts/*/application`): One Use Case = one business action. Single `execute(dto)` method. Inject abstract repositories, NEVER concrete classes.
- **Infrastructure** (`src/contexts/*/infrastructure`): SQLAlchemy models, repository implementations, HTTP middleware, CLI commands, and DI containers.

## Directory Structure per Context

```
src/contexts/<context>/
├── domain/
│   ├── aggregates.py      # Entities extending AggregateRoot (Pydantic)
│   ├── repositories.py    # Abstract repository interfaces (ABC)
│   └── errors.py          # Domain-specific exceptions
├── application/
│   └── use_cases/         # One file per use case
│       └── <action>.py    # Class with execute(dto) method
└── infrastructure/
    ├── container.py       # DI container for this context
    ├── persistence/
    │   ├── models.py      # SQLAlchemy ORM models
    │   └── <name>_repository.py  # Concrete repository
    ├── http/              # FastAPI middleware/dependencies
    └── cli/               # Typer CLI commands
```

## Dependency Injection

- Uses `dependency-injector` with declarative containers.
- Root container: `src/container.py` (`ApplicationContainer`) composes context containers.
- Each context has its own container (e.g., `AuthContainer`) that declares repositories and use cases as `providers.Factory`.
- Cross-context dependencies flow through `providers.DependenciesContainer()` (e.g., `shared` provides `session_factory` and `cache_client` to `AuthContainer`).
- Wiring happens at app startup in `lifespan()` — only wire modules that use `@inject`.

## Repository Pattern

- Interfaces: `abstract class` (ABC) in `domain/repositories.py` with async methods.
- Implementations: `<Name>SQLAlchemyRepository` in `infrastructure/persistence/`, using `sessionmaker` and `AsyncSession`.
- Use `selectinload` for eager-loading relationships (avoid N+1).
- Repositories handle transaction scope via session context manager.

## Caching

- Abstract interface: `CacheClient` at `src/contexts/shared/domain/cache_client.py` — a string store (`get`/`set`/`delete`/`clear`).
- Production implementation: `RedisCacheClient` (`src/contexts/shared/infrastructure/cache/redis_cache_client.py`), backed by `redis.asyncio`. Keys are namespaced under a prefix; Redis errors degrade gracefully (logged warning, `get` returns `None`, writes become no-ops).
- Test double: `InMemoryCacheClient` (TTL-based dict), injected via `override_container` in tests.
- Callers serialize: repositories store `model_dump_json()` and read back with `Model.model_validate_json(...)`.
- Cache key pattern: `api_key:{key_hash}` (default 600s TTL).
- Configured via `REDIS_URL`; reported as a soft component in `/health` (the database is the only hard dependency).

## Public Route Decorator

- The `@public` decorator (`src/contexts/shared/infrastructure/http/public_decorator.py`) marks endpoints that bypass API key authentication.
- It sets `endpoint.is_public = True`, which the `verify_api_key` middleware checks.
- Apply it directly on the route function, AFTER the `@app.get`/`@app.post` decorator.

## Error Handling

- Domain/Application: throw domain errors (e.g., `InvalidApiKeyError`, `UserNotFoundError`), NEVER `HTTPException`.
- Domain errors propagate naturally through middleware and are caught by the global `domain_error_handler` registered via `register_exception_handlers(app)` in `main.py`.
- `ERROR_STATUS_MAP` in `src/contexts/shared/infrastructure/http/exception_handlers.py` maps base error types to HTTP status codes (`NotFoundError` → 404, `UnauthorizedError` → 401, `ForbiddenError` → 403, `ConflictError` → 409). Unmatched `DomainError` subclasses fall back to 400.
- To add a new HTTP status code mapping, add an entry to `ERROR_STATUS_MAP`. To add a new domain error, just inherit from the appropriate base class and it will be handled automatically.
- Context-specific errors inherit from shared base errors (e.g., `InvalidApiKeyError(UnauthorizedError)`, `UserNotFoundError(NotFoundError)`). No context-specific catch-all base class needed.

## SQLAlchemy Models

- Base model at `src/contexts/shared/infrastructure/persistence/base.py` with metadata naming conventions (`ix_`, `uq_`, `fk_`, `ck_`, `pk_`).
- All timestamps use UTC (`datetime.now(UTC)`), stored with timezone info.
- Foreign keys use `ondelete="CASCADE"` where appropriate.
- Server defaults for `created_at` and `updated_at` via `func.now()`.

## Aggregate Methods

- All state-mutating methods must update `self.updated_at = datetime.now(UTC)`.
- Use imperative verb form: `revoke_api_key`, not `revoked_api_key`.
- Factory methods use `@staticmethod` named `create(...)`.
