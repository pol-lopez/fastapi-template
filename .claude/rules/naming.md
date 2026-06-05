---
description: File, class, and method naming conventions
paths: ["src/**"]
---

# Naming Conventions

All names in English. Files are `snake_case`, classes are `PascalCase`, functions / methods / variables are `snake_case`.

## File Naming

| Element                   | File                       | Example                               |
| ------------------------- | -------------------------- | ------------------------------------- |
| Aggregates / entities     | `aggregates.py`            | `aggregates.py`                       |
| Repository interfaces     | `repositories.py`          | `repositories.py`                     |
| Domain errors             | `errors.py`                | `errors.py`                           |
| Domain events             | `events.py`                | `events.py`                           |
| Domain services           | `services.py`              | `services.py`                         |
| Use case                  | `<verb>_<noun>.py`         | `create_user.py`, `revoke_api_key.py` |
| CLI command               | `<verb>_<noun>_command.py` | `create_user_command.py`              |
| SQLAlchemy models         | `models.py`                | `models.py`                           |
| Repository implementation | `<entity>_repository.py`   | `user_repository.py`                  |
| DI container              | `container.py`             | `container.py`                        |
| HTTP router               | `router.py`                | `router.py`                           |
| Middleware                | `<name>_middleware.py`     | `api_key_middleware.py`               |
| Decorator                 | `<name>_decorator.py`      | `public_decorator.py`                 |

## Class Naming

| Element                      | Pattern                                   | Example                            |
| ---------------------------- | ----------------------------------------- | ---------------------------------- |
| Aggregate root               | `<Entity>(AggregateRoot)`                 | `User`                             |
| Nested entity / value object | `<Name>(BaseModel)`                       | `ApiKey`                           |
| Repository interface         | `<Entity>Repository` (ABC)                | `UserRepository`                   |
| Repository implementation    | `<Entity>SQLAlchemyRepository`            | `UserSQLAlchemyRepository`         |
| Use case                     | `<Action>UseCase`                         | `CreateUserUseCase`                |
| Use case DTO                 | `<Action>DTO`                             | `CreateUserDTO`                    |
| Domain error                 | `<Specific>Error` (extends a shared base) | `UserNotFoundError(NotFoundError)` |
| DI container                 | `<Context>Container`                      | `AuthContainer`                    |
| Domain service               | noun, `PascalCase`                        | `ApiKeyHasher`                     |

## Method & Function Naming

- Aggregate state-mutating methods: imperative verb — `revoke_api_key`, not `revoked_api_key`.
- Factory methods: `@staticmethod` named `create(...)`.
- Use case entry point: a single `execute(dto)` method.
- CLI command registration: `register_<verb>_<noun>_command(app)`.
- Domain errors inherit from the shared base errors (`NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError`).
