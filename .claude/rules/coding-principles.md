---
description: Design and coding principles for writing production code
paths: ["src/**"]
---

# Coding Principles

## SOLID (applied to this project)

- **SRP**: One Use Case = one business action. One middleware = one concern. If a class has more than one reason to change, split it.
- **OCP**: Add new Use Cases instead of modifying existing ones. Use strategy pattern for variable behavior.
- **LSP**: Repository implementations must honor exactly the abstract class contract.
- **ISP**: Keep repository interfaces minimal. Prefer several small interfaces over one large one.
- **DIP**: Always inject abstract classes (repositories/ports), never concrete implementations. Use `dependency-injector` providers.

## Tell Don't Ask

Call methods on the entity that encapsulate the decision. Do NOT extract entity state to decide outside.

- BAD: `if not api_key.is_active: raise InactiveApiKeyError()`
- GOOD: `user.revoke_api_key(api_key_id)` (the entity validates internally)

## DDD

- Business logic lives in entities/aggregates, NOT in use cases or services.
- Use Cases orchestrate (call entity methods and repos); entities decide.
- Respect bounded context boundaries: do not import domain from another context directly — use ports/interfaces.
- Ubiquitous Language: class names, method names, and variables must reflect the domain language.

## Command-Query Separation

- Methods either change state OR return data, never both.
- Queries must have no side effects.

## KISS / YAGNI / DRY

- Prefer clarity over brevity. No complex one-liners.
- Implement ONLY what is needed now. No speculative features.
- Extract shared logic to `src/contexts/shared`. But do NOT DRY across bounded contexts unless it is truly shared infrastructure.
- Do not create abstractions for a single use. Do not add configurability without real use cases.

## Law of Demeter

Do not chain calls through nested objects — instead, expose methods on the aggregate.

## Python-Specific

- Use Pydantic `BaseModel` for domain entities and DTOs. Use `Field(...)` for required fields, `Field(default=...)` for optional.
- Use `from __future__ import annotations` only if needed for forward refs. Prefer `"ClassName"` string annotations.
- Use `list[X]`, `dict[K, V]`, `X | None` syntax (not `List`, `Dict`, `Optional` from typing).
- Async all the way: if a function does I/O, it must be `async`. Do not mix sync DB calls with async endpoints.
- Use `datetime.now(UTC)` for timestamps, never `datetime.utcnow()` (deprecated).
