import uuid

from app.infrastructure.db.models.user_settings import UserSettings
from app.infrastructure.db.repositories.user_settings_repository import (
    UserSettingsRepository,
)


async def update_user_settings(
    repository: UserSettingsRepository,
    user_id: uuid.UUID,
    *,
    display_name: str | None,
    timezone: str,
    theme: str,
) -> UserSettings:
    return await repository.update(
        user_id,
        display_name=display_name,
        timezone=timezone,
        theme=theme,
    )