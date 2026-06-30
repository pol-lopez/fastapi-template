import redis.asyncio as redis
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.contexts.shared.application.use_cases.check_health import CheckHealthUseCase
from src.contexts.shared.infrastructure.cache import RedisCacheClient
from src.contexts.shared.infrastructure.cache.redis_health_checker import (
    RedisHealthChecker,
)
from src.contexts.shared.infrastructure.events.in_memory_event_bus import (
    InMemoryEventBus,
)
from src.contexts.shared.infrastructure.persistence.database_health_checker import (
    DatabaseHealthChecker,
)
from src.settings import settings


class SharedContainer(containers.DeclarativeContainer):
    engine = providers.Singleton(
        create_async_engine,
        url=settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        connect_args={"command_timeout": settings.database_command_timeout},
    )

    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    redis_client = providers.Singleton(
        redis.from_url,
        url=settings.redis_url,
        decode_responses=True,
    )

    cache_client = providers.Singleton(
        RedisCacheClient,
        client=redis_client,
    )

    event_bus = providers.Singleton(
        InMemoryEventBus,
    )

    database_health_checker = providers.Factory(
        DatabaseHealthChecker,
        session_factory=session_factory,
    )

    cache_health_checker = providers.Factory(
        RedisHealthChecker,
        client=redis_client,
    )

    check_health_use_case = providers.Factory(
        CheckHealthUseCase,
        database_checker=database_health_checker,
        cache_checker=cache_health_checker,
    )
