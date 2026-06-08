import pytest

from src.contexts.auth.application.use_cases.authenticate_with_api_key import (
    AuthenticatedIdentity,
    AuthenticateWithApiKeyDTO,
    AuthenticateWithApiKeyUseCase,
)
from src.contexts.auth.domain.errors import InactiveApiKeyError, InvalidApiKeyError
from src.contexts.auth.domain.services import ApiKeyHasher
from tests.contexts.auth.conftest import FakeUserRepository
from tests.support.factories import UserFactory


@pytest.mark.unit
class TestAuthenticateWithApiKeyUseCase:
    async def test_authenticates_with_valid_key_returns_identity(
        self,
        fake_user_repository: FakeUserRepository,
    ) -> None:
        user, plain_key = UserFactory.with_api_key()
        await fake_user_repository.save(user)
        use_case = AuthenticateWithApiKeyUseCase(fake_user_repository)

        identity = await use_case.execute(AuthenticateWithApiKeyDTO(api_key=plain_key))

        assert isinstance(identity, AuthenticatedIdentity)
        assert identity.user_id == user.user_id
        assert identity.api_key_id == user.api_keys[0].api_key_id

    async def test_raises_error_for_invalid_key(
        self, fake_user_repository: FakeUserRepository
    ) -> None:
        use_case = AuthenticateWithApiKeyUseCase(fake_user_repository)

        with pytest.raises(InvalidApiKeyError):
            await use_case.execute(AuthenticateWithApiKeyDTO(api_key="invalid"))

    async def test_raises_error_for_inactive_key(
        self,
        fake_user_repository: FakeUserRepository,
    ) -> None:
        user, plain_key = UserFactory.with_api_key()
        key_hash = ApiKeyHasher.hash(plain_key)
        api_key_entity = user.find_api_key_by_hash(key_hash)
        assert api_key_entity is not None
        user.revoke_api_key(api_key_entity.api_key_id)
        await fake_user_repository.save(user)
        use_case = AuthenticateWithApiKeyUseCase(fake_user_repository)

        with pytest.raises(InactiveApiKeyError):
            await use_case.execute(AuthenticateWithApiKeyDTO(api_key=plain_key))
