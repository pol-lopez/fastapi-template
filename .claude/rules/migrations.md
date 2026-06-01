---
description: Alembic migration conventions for PostgreSQL
paths: ["migrations/**"]
---

# Migrations (Alembic)

## Creating & Applying

- Autogenerate after changing models: `make migration-create` (prompts for a message). **Review the output** — autogenerate is a starting point, not final.
- Empty migration: `make migration-create-empty`.
- Apply: `make migration-upgrade`. Rollback last: `make migration-downgrade`.
- Inspect: `make migration-history`, `make migration-current`, `make migration-show`.

## File Naming

- Files live in `migrations/versions/`.
- Name template (set by `file_template` in `alembic.ini`): `YYYYMMDD_HHMM-<rev>_<slug>.py` — e.g. `20260117_1015-ee87a42a42a5_enable_key_timezone.py`. Do not rename manually.

## Structure

- Implement BOTH `upgrade()` and `downgrade()`. Never leave `downgrade()` as `pass` — it must reverse `upgrade()`.
- Revision identifiers are typed: `revision: str`, `down_revision: str | Sequence[str] | None`.
- Use `op` for DDL and `sa` / `sqlalchemy.dialects.postgresql` for column types.

## Conventions

- Timestamps: `sa.DateTime(timezone=True)` (UTC, timezone-aware), server defaults via `sa.text("now()")`.
- Foreign keys: `ondelete="CASCADE"` where appropriate.
- Rely on the metadata naming convention (`ix_`, `uq_`, `fk_`, `ck_`, `pk_`) from `src/contexts/shared/infrastructure/persistence/base.py` — do not hardcode constraint names.
- Keep column `comment=` in sync with the models.
- Data migrations: prefer separating schema changes from data backfills; use `op.execute()` for data and make them idempotent.

## Don'ts

- Don't edit a migration that's already applied/merged — add a new one.
- Don't trust autogenerate blindly: it misses enum changes, some server-side defaults, and certain constraint renames.
