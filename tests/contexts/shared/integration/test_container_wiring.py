import pytest

from src.contexts.shared.infrastructure.cache import RedisCacheClient
from src.main import container


@pytest.mark.integration
def test_production_container_resolves_redis_cache_client() -> None:
    assert isinstance(container.shared_container.cache_client(), RedisCacheClient)
