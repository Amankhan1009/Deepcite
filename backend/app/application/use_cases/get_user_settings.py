import uuid

from app.infrastructure.db.models.user_settings import UserSettings
from app.infrastructure.db.repositories.user_settings_repository import (
    UserSettingsRepository,
)


async def get_user_settings(
    repository: UserSettingsRepository,
    user_id: uuid.UUID,
) -> UserSettings:
    return await repository.get_or_create(user_id)