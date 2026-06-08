from dataclasses import dataclass
from uuid import UUID

from src.contexts.auth.domain.errors import InactiveApiKeyError, InvalidApiKeyError
from src.contexts.auth.domain.repositories import UserRepository
from src.contexts.auth.domain.services import ApiKeyHasher


@dataclass(frozen=True, slots=True)
class AuthenticateWithApiKeyDTO:
    api_key: str


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    user_id: UUID
    api_key_id: UUID


class AuthenticateWithApiKeyUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(self, dto: AuthenticateWithApiKeyDTO) -> AuthenticatedIdentity:
        key_hash = ApiKeyHasher.hash(dto.api_key)
        api_key = await self.user_repository.find_api_key_by_hash(key_hash)

        if not api_key:
            raise InvalidApiKeyError

        if not api_key.is_active:
            raise InactiveApiKeyError

        return AuthenticatedIdentity(
            user_id=api_key.user_id,
            api_key_id=api_key.api_key_id,
        )
