from uuid import uuid4

import pytest

from src.container import ApplicationContainer
from src.contexts.auth.domain.aggregates import ApiKey
from src.contexts.auth.domain.repositories import UserRepository
from src.contexts.auth.domain.services import ApiKeyHasher
from src.contexts.shared.domain.pagination import CursorParams
from src.contexts.shared.infrastructure.cache import InMemoryCacheClient
from tests.support.factories import PersistentUserFactory, UserFactory


@pytest.fixture
def user_repository(override_container: ApplicationContainer) -> UserRepository:
    return override_container.auth_container.user_repository()


@pytest.fixture
def cache_client(override_container: ApplicationContainer) -> InMemoryCacheClient:
    return override_container.shared_container.cache_client()


@pytest.mark.integration
class TestUserRepositoryCRUD:
    async def test_save_and_find_by_id(self, user_repository: UserRepository) -> None:
        user = UserFactory.build()
        await user_repository.save(user)

        found = await user_repository.find_by_id(user.user_id)

        assert found is not None
        assert found.user_id == user.user_id
        assert found.username == user.username
        assert found.email == user.email
        assert found.password == user.password
        assert found.is_active == user.is_active

    async def test_find_by_username(self, user_repository: UserRepository) -> None:
        user = UserFactory.build()
        await user_repository.save(user)

        found = await user_repository.find_by_username(user.username)

        assert found is not None
        assert found.user_id == user.user_id

    async def test_find_by_id_returns_none_for_nonexistent(
        self, user_repository: UserRepository
    ) -> None:
        found = await user_repository.find_by_id(uuid4())

        assert found is None

    async def test_update_existing_user(self, user_repository: UserRepository) -> None:
        user = UserFactory.build()
        await user_repository.save(user)

        user.username = "updated-username"
        user.email = "updated@test.com"
        await user_repository.save(user)

        found = await user_repository.find_by_id(user.user_id)
        assert found is not None
        assert found.username == "updated-username"
        assert found.email == "updated@test.com"

    async def test_delete_user(self, user_repository: UserRepository) -> None:
        user = UserFactory.build()
        await user_repository.save(user)

        await user_repository.delete(user.user_id)

        found = await user_repository.find_by_id(user.user_id)
        assert found is None


@pytest.mark.integration
class TestUserRepositoryORMMapping:
    async def test_roundtrip_with_api_keys(
        self, user_repository: UserRepository
    ) -> None:
        user, plain_key = UserFactory.with_api_key()
        await user_repository.save(user)

        found = await user_repository.find_by_id(user.user_id)

        assert found is not None
        assert len(found.api_keys) == 1
        api_key = found.api_keys[0]
        assert api_key.user_id == user.user_id
        assert api_key.key_hash == ApiKeyHasher.hash(plain_key)
        assert api_key.is_active is True

    async def test_roundtrip_with_multiple_api_keys(
        self, user_repository: UserRepository
    ) -> None:
        user, keys = UserFactory.with_n_api_keys(3)
        await user_repository.save(user)

        found = await user_repository.find_by_id(user.user_id)

        assert found is not None
        assert len(found.api_keys) == 3
        found_hashes = {k.key_hash for k in found.api_keys}
        expected_hashes = {ApiKeyHasher.hash(k) for k in keys}
        assert found_hashes == expected_hashes


@pytest.mark.integration
class TestUserRepositoryCache:
    async def test_find_api_key_by_hash_populates_cache(
        self,
        user_repository: UserRepository,
        cache_client: InMemoryCacheClient,
    ) -> None:
        user, plain_key = UserFactory.with_api_key()
        await user_repository.save(user)
        key_hash = ApiKeyHasher.hash(plain_key)

        result = await user_repository.find_api_key_by_hash(key_hash)

        assert result is not None
        assert result.key_hash == key_hash

        cached = await cache_client.get(f"api_key:{key_hash}")
        assert cached is not None

    async def test_save_caches_api_key_as_serialized_json(
        self,
        user_repository: UserRepository,
        cache_client: InMemoryCacheClient,
    ) -> None:
        user, plain_key = UserFactory.with_api_key()
        await user_repository.save(user)
        key_hash = ApiKeyHasher.hash(plain_key)

        cached = await cache_client.get(f"api_key:{key_hash}")

        assert isinstance(cached, str)
        assert ApiKey.model_validate_json(cached).key_hash == key_hash

    async def test_cache_invalidation_on_delete(
        self,
        user_repository: UserRepository,
        cache_client: InMemoryCacheClient,
    ) -> None:
        user, plain_key = UserFactory.with_api_key()
        await user_repository.save(user)
        key_hash = ApiKeyHasher.hash(plain_key)

        cached = await cache_client.get(f"api_key:{key_hash}")
        assert cached is not None

        await user_repository.delete(user.user_id)

        cached_after = await cache_client.get(f"api_key:{key_hash}")
        assert cached_after is None


@pytest.mark.integration
class TestUserRepositoryPagination:
    async def test_cursor_pagination_forward(
        self,
        user_repository: UserRepository,
        user_factory: PersistentUserFactory,
    ) -> None:
        users = await user_factory.create_batch(5)
        created_ids = {u.user_id for u in users}

        page1 = await user_repository.list_paginated(CursorParams(page_size=3))

        assert len(page1.items) >= 2
        assert page1.next_cursor is not None
        page1_ids = {u.user_id for u in page1.items}

        page2 = await user_repository.list_paginated(
            CursorParams(cursor=page1.next_cursor, page_size=3)
        )

        assert len(page2.items) >= 1
        assert page2.previous_cursor is not None
        page2_ids = {u.user_id for u in page2.items}

        assert page1_ids.isdisjoint(page2_ids)
        assert created_ids <= (page1_ids | page2_ids)

    async def test_cursor_pagination_backward(
        self,
        user_repository: UserRepository,
        user_factory: PersistentUserFactory,
    ) -> None:
        await user_factory.create_batch(5)

        page1 = await user_repository.list_paginated(CursorParams(page_size=3))
        assert page1.next_cursor is not None

        page2 = await user_repository.list_paginated(
            CursorParams(cursor=page1.next_cursor, page_size=3)
        )
        assert page2.previous_cursor is not None

        prev_page = await user_repository.list_paginated(
            CursorParams(cursor=page2.previous_cursor, page_size=3)
        )

        assert len(prev_page.items) == len(page1.items)
        prev_ids = [u.user_id for u in prev_page.items]
        page1_ids = [u.user_id for u in page1.items]
        assert prev_ids == page1_ids


@pytest.mark.integration
class TestUserRepositoryCascade:
    async def test_delete_user_cascades_to_api_keys(
        self, user_repository: UserRepository
    ) -> None:
        user, keys = UserFactory.with_n_api_keys(2)
        await user_repository.save(user)

        await user_repository.delete(user.user_id)

        found = await user_repository.find_by_id(user.user_id)
        assert found is None

        for key in keys:
            key_hash = ApiKeyHasher.hash(key)
            api_key = await user_repository.find_api_key_by_hash(key_hash)
            assert api_key is None
