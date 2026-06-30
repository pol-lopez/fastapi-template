import os

# One worker per CPU core (best for async UvicornWorker); WEB_CONCURRENCY overrides it.
# ponytail: os.cpu_count() reads host cores, not the cgroup CPU limit — in a
# CPU-limited container (e.g. k8s) set WEB_CONCURRENCY to match the limit.
workers = int(os.environ.get("WEB_CONCURRENCY", os.cpu_count() or 1))

# Load the app once in the master and fork workers (copy-on-write) — ~halves RAM
# with many workers. Safe here: the SQLAlchemy engine and Redis client are lazy
# singletons and connections open post-fork (per-worker lifespan), not at import.
preload_app = True
