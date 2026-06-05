---
description: Git commit, branch, and push conventions
---

# Git Conventions

## Commits

- Conventional Commits with gitmoji (commitizen `cz_gitmoji`). Format: `<emoji> <type>(<scope>): <subject>` — e.g. `:bug: fix(auth): handle inactive key edge case`.
- Subject in English, imperative mood ("add", "fix", "remove" — not "added"/"fixes").
- Scope = bounded context or area (`auth`, `shared`, `migrations`).
- NEVER propose or execute a commit unless explicitly asked.
- NEVER use `--no-verify` on commit or push.

## Branches

- All work on a branch — NEVER commit to `main`.
- Prefixes: `feature/`, `fix/`, `perf/`, `refactor/`, `chore/`.

## Pushing

- NEVER force-push; NEVER push directly to `main`. Open a PR from the feature branch.
