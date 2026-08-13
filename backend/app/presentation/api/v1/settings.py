from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.get_user_settings import get_user_settings
from app.application.use_cases.update_user_settings import update_user_settings
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.user_settings_repository import (
    UserSettingsRepository,
)
from app.infrastructure.db.session import get_db
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.settings import (
    UpdateSettingsRequest,
    UserSettingsResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "",
    response_model=UserSettingsResponse,
)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = await get_user_settings(
        UserSettingsRepository(db),
        current_user.id,
    )

    return UserSettingsResponse.model_validate(settings)


@router.patch(
    "",
    response_model=UserSettingsResponse,
)
async def patch_settings(
    payload: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = await update_user_settings(
        UserSettingsRepository(db),
        current_user.id,
        display_name=payload.display_name,
        timezone=payload.timezone,
        theme=payload.theme,
    )

    return UserSettingsResponse.model_validate(settings)