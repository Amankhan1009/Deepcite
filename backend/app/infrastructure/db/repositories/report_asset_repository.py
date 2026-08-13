import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.report_asset import ReportAsset


class ReportAssetRepository:
    """Database access for generated report assets."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        report_id: uuid.UUID,
        asset_type: str,
        file_path: str,
        caption: str | None = None,
    ) -> ReportAsset:
        asset = ReportAsset(
            report_id=report_id,
            asset_type=asset_type,
            file_path=file_path,
            caption=caption,
        )

        self.session.add(asset)
        await self.session.commit()
        await self.session.refresh(asset)

        return asset

    async def list_for_report(
        self,
        report_id: uuid.UUID,
    ) -> list[ReportAsset]:
        result = await self.session.execute(
            select(ReportAsset)
            .where(ReportAsset.report_id == report_id)
            .order_by(ReportAsset.created_at)
        )

        return list(result.scalars().all())