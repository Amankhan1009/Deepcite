import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.user_settings import UserSettings


class UserSettingsRepository:
    """Database access for persisted user settings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self,
        user_id: uuid.UUID,
    ) -> UserSettings:
        result = await self.session.execute(
            select(UserSettings).where(
                UserSettings.user_id == user_id,
            )
        )

        settings = result.scalar_one_or_none()

        if settings is not None:
            return settings

        settings = UserSettings(user_id=user_id)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)

        return settings

    async def update(
        self,
        user_id: uuid.UUID,
        *,
        display_name: str | None,
        timezone: str,
        theme: str,
    ) -> UserSettings:
        settings = await self.get_or_create(user_id)

        settings.display_name = display_name
        settings.timezone = timezone
        settings.theme = theme

        await self.session.commit()
        await self.session.refresh(settings)

        return settings