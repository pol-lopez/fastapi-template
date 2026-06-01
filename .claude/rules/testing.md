---
description: Testing conventions for unit, integration, and e2e tests
paths: ["tests/**", "**/*test*.py"]
---

# Testing Conventions

## Test Structure

Tests mirror the source structure under `tests/contexts/<context>/`:

- `unit/` — Fast tests, no I/O, no DB
- `integration/` — Require running database (Docker)
- `e2e/` — Full HTTP flow via `AsyncClient`

## Markers

Every test file or class MUST be decorated with the appropriate pytest marker:

- `@pytest.mark.unit` — No external dependencies
- `@pytest.mark.integration` — Needs database
- `@pytest.mark.e2e` — Full app flow
- `@pytest.mark.slow` — Long-running tests

## Unit Tests

- Test aggregate behavior, not implementation details.
- Instantiate domain objects directly — no mocking framework needed for pure domain logic.
- NEVER touch DB or I/O.
- Run with: `make test-unit` (Docker) or `make test-unit-local` (local, fast).

## Integration Tests

- Located in `tests/contexts/<context>/integration/`.
- Require Docker services running (`make start`).
- Test repository implementations against real PostgreSQL.
- Run with: `make test-integration`.

## E2E Tests

- Located in `tests/contexts/<context>/e2e/`.
- Use the `client` fixture (`AsyncClient` with `ASGITransport`).
- Test full HTTP request/response cycle including middleware.
- Run with: `make test-e2e`.

## Shared Test Infrastructure (`tests/support/`)

- `tests/support/database.py` — `test_engine` (session-scoped, NullPool), `test_transaction` (function-scoped, rollback after each test), `test_session_factory` (savepoint-based).
- `tests/support/containers.py` — `override_container` fixture overrides the production `ApplicationContainer` with test engine/session/cache. `user_factory` fixture provides `PersistentUserFactory`.
- `tests/support/factories.py` — `UserFactory` (in-memory domain aggregates) and `PersistentUserFactory` (persisted to DB).

All support fixtures are registered in `tests/conftest.py` for automatic pytest discovery across all test suites.

## Factories

- Use `UserFactory.build()` for unit tests (pure domain, no DB).
- Use `UserFactory.with_api_key()` / `UserFactory.with_n_api_keys(n)` for users with API keys.
- Use `PersistentUserFactory` (via `user_factory` fixture) for integration tests that need persisted data.
- Do NOT use hardcoded fixtures like `sample_user`. Always use factories for randomized test data.

## Test Isolation (Integration & E2E)

- Transaction rollback pattern: each test runs inside a DB transaction that is rolled back after the test.
- `join_transaction_mode="create_savepoint"` ensures application `session.commit()` calls create savepoints instead of committing the outer transaction.
- `override_container` overrides `session_factory`, `engine`, and `cache_client` (fresh `InMemoryCacheClient` per test) on the production container.

## Fixtures

- `app` — FastAPI app instance (from `src.main`).
- `client` — `httpx.AsyncClient` bound to the app via ASGI transport, base URL `http://test`. Depends on `override_container`.
- `override_container` — Production container with test DB overrides.
- `user_factory` — `PersistentUserFactory` wired to the overridden repository.
- `fake_user_repository` — In-memory `FakeUserRepository` for unit tests.
- Shared fixtures live in `tests/support/` and are registered in `tests/conftest.py`. Context-specific fixtures go in their own `conftest.py`.

## Async

- `asyncio_mode = "auto"` is configured — no need for `@pytest.mark.asyncio` on every test.
- Fixture loop scope: `function` (each test gets its own event loop).

## Conventions

- File naming: `test_<subject>.py`.
- Class naming: `Test<Subject>`.
- Function naming: `test_<behavior_description>`.
- Use descriptive test names that explain the expected behavior: `test_revoke_api_key_returns_false_when_key_not_found`.
- One assertion per test when possible. Multiple assertions are fine if testing the same logical outcome.
