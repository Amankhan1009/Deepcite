import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.confidence_scoring import (
    calculate_claim_confidence,
    calculate_overall_confidence,
)
from app.domain.services.evaluation_scoring import calculate_report_quality
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.repositories.citation_repository import (
    CitationRepository,
)
from app.infrastructure.db.repositories.claim_repository import ClaimRepository
from app.infrastructure.db.repositories.evaluation_repository import (
    EvaluationRepository,
)
from app.infrastructure.db.repositories.evidence_repository import (
    EvidenceRepository,
)
from app.infrastructure.db.repositories.report_asset_repository import (
    ReportAssetRepository,
)
from app.infrastructure.db.repositories.report_repository import ReportRepository
from app.infrastructure.db.repositories.research_plan_repository import (
    ResearchPlanRepository,
)
from app.infrastructure.db.repositories.source_repository import SourceRepository


def _reliabilities_for_evidence_indexes(
    evidence_indexes: list[int],
    evidence_items: list[dict],
    source_by_index: dict,
) -> list[float]:
    reliabilities: list[float] = []

    for evidence_index in evidence_indexes:
        if evidence_index >= len(evidence_items):
            continue

        source_index = evidence_items[evidence_index].get("source_index")
        source = source_by_index.get(source_index)

        if source is not None:
            reliabilities.append(
                float(source.reliability_score or 0.0),
            )

    return reliabilities


def _reliabilities_for_source_indexes(
    source_indexes: set[int],
    source_by_index: dict,
) -> list[float]:
    return [
        float(source_by_index[source_index].reliability_score or 0.0)
        for source_index in source_indexes
        if source_index in source_by_index
    ]


async def persist_research_artifacts(
    db: AsyncSession,
    run: ResearchRun,
    result: dict,
) -> None:
    """Persist research artifacts without creating duplicates on resume."""

    plan = result.get("plan")
    plan_repository = ResearchPlanRepository(db)

    existing_plan = await plan_repository.get_for_research_run(run.id)

    if plan is not None and existing_plan is None:
        await plan_repository.create(
            research_run_id=run.id,
            sub_questions=plan["sub_questions"],
            strategy=plan["strategy"],
        )

    sources = result.get("verified_sources") or result.get("sources") or []
    source_repository = SourceRepository(db)
    existing_sources = await source_repository.list_for_research_run(run.id)

    source_by_index = {
        index: source
        for index, source in enumerate(existing_sources)
    }

    for index, source in enumerate(sources):
        source_index = source.get("source_index", index)

        if source_index in source_by_index:
            continue

        persisted_source = await source_repository.create(
            research_run_id=run.id,
            url=source["url"],
            title=source.get("title"),
            raw_content_ref=source.get("content"),
            reliability_score=source.get("reliability_score"),
        )

        source_by_index[source_index] = persisted_source

    evidence_items = result.get("evidence") or []
    evidence_repository = EvidenceRepository(db)
    existing_evidence = await evidence_repository.list_for_research_run(run.id)

    evidence_by_index = {
        index: evidence
        for index, evidence in enumerate(existing_evidence)
    }

    evidence_by_source_index: dict[int, list[str]] = {}

    for evidence in evidence_by_index.values():
        source_index = next(
            (
                source_index
                for source_index, source in source_by_index.items()
                if source.id == evidence.source_id
            ),
            None,
        )

        if source_index is not None:
            evidence_by_source_index.setdefault(
                source_index,
                [],
            ).append(str(evidence.id))

    for evidence_index, item in enumerate(evidence_items):
        if evidence_index in evidence_by_index:
            continue

        source = source_by_index.get(item["source_index"])

        if source is None:
            continue

        evidence = await evidence_repository.create(
            research_run_id=run.id,
            source_id=source.id,
            claim_text=item["claim_text"],
        )

        evidence_by_index[evidence_index] = evidence
        evidence_by_source_index.setdefault(
            item["source_index"],
            [],
        ).append(str(evidence.id))

    reasoning_data = result.get("reasoning") or {}
    reasoning_items = reasoning_data.get("items") or []
    fact_checks_data = result.get("fact_checks") or {}
    fact_check_items = fact_checks_data.get("items") or []

    claim_repository = ClaimRepository(db)
    existing_claims = await claim_repository.list_for_research_run(run.id)

    if reasoning_items and not existing_claims:
        fact_checks_by_claim_index = {
            item["claim_index"]: item
            for item in fact_check_items
            if "claim_index" in item
        }

        fallback_supporting_source_indexes = set(
            reasoning_data.get("supporting_source_indexes") or [],
        )
        fallback_contradicting_source_indexes = set(
            reasoning_data.get("contradicting_source_indexes") or [],
        )

        evidence_ids_by_index = {
            index: str(evidence.id)
            for index, evidence in evidence_by_index.items()
        }

        for claim_index, claim_text in enumerate(reasoning_items):
            fact_check = fact_checks_by_claim_index.get(claim_index)

            if fact_check is not None:
                supporting_evidence_indexes = (
                    fact_check.get("supporting_evidence_indexes") or []
                )
                contradicting_evidence_indexes = (
                    fact_check.get("contradicting_evidence_indexes") or []
                )

                supporting_evidence_ids = [
                    evidence_ids_by_index[evidence_index]
                    for evidence_index in supporting_evidence_indexes
                    if evidence_index in evidence_ids_by_index
                ]

                contradicting_evidence_ids = [
                    evidence_ids_by_index[evidence_index]
                    for evidence_index in contradicting_evidence_indexes
                    if evidence_index in evidence_ids_by_index
                ]

                fact_check_status = fact_check.get(
                    "status",
                    "uncertain",
                )

                supporting_reliabilities = (
                    _reliabilities_for_evidence_indexes(
                        supporting_evidence_indexes,
                        evidence_items,
                        source_by_index,
                    )
                )
                contradicting_reliabilities = (
                    _reliabilities_for_evidence_indexes(
                        contradicting_evidence_indexes,
                        evidence_items,
                        source_by_index,
                    )
                )
            else:
                supporting_evidence_ids = [
                    evidence_id
                    for source_index in fallback_supporting_source_indexes
                    for evidence_id in evidence_by_source_index.get(
                        source_index,
                        [],
                    )
                ]

                contradicting_evidence_ids = [
                    evidence_id
                    for source_index in fallback_contradicting_source_indexes
                    for evidence_id in evidence_by_source_index.get(
                        source_index,
                        [],
                    )
                ]

                fact_check_status = "unverified"

                supporting_reliabilities = (
                    _reliabilities_for_source_indexes(
                        fallback_supporting_source_indexes,
                        source_by_index,
                    )
                )
                contradicting_reliabilities = (
                    _reliabilities_for_source_indexes(
                        fallback_contradicting_source_indexes,
                        source_by_index,
                    )
                )

            confidence_score = calculate_claim_confidence(
                status=fact_check_status,
                supporting_source_reliabilities=supporting_reliabilities,
                contradicting_source_reliabilities=(
                    contradicting_reliabilities
                ),
            )

            await claim_repository.create(
                research_run_id=run.id,
                text=claim_text,
                supporting_evidence_ids=supporting_evidence_ids,
                contradicting_evidence_ids=contradicting_evidence_ids,
                fact_check_status=fact_check_status,
                confidence_score=confidence_score,
            )


def _referenced_source_positions(
    report_markdown: str,
) -> set[int]:
    """Return the source positions explicitly cited in report Markdown."""

    return {
        int(match)
        for match in re.findall(
            r"(?:\[|\()Source\s+(\d+)(?:\]|\))",
            report_markdown,
            flags=re.IGNORECASE,
        )
    }

async def persist_report_result(
    db: AsyncSession,
    run: ResearchRun,
    result: dict,
) -> None:
    """Persist report, confidence, citations, and chart asset once."""

    report_data = result.get("report")

    if report_data is None:
        return

    report_repository = ReportRepository(db)

    existing_report = await report_repository.get_for_research_run(run.id)

    if existing_report is not None:
        return

    claim_repository = ClaimRepository(db)
    claims = await claim_repository.list_for_research_run(run.id)

    overall_confidence_score = calculate_overall_confidence(
        claim.confidence_score
        for claim in claims
    )

    chart_asset = result.get("chart_asset")
    content_markdown = report_data["content_markdown"]
    referenced_source_positions = _referenced_source_positions(
        content_markdown,
    )

    if chart_asset is not None:
        content_markdown = (
            f"{content_markdown}\n\n"
            f"![{chart_asset['caption']}]"
            f"({chart_asset['file_path']})"
        )

    report = await report_repository.create(
        research_run_id=run.id,
        content_markdown=content_markdown,
        executive_summary=report_data["executive_summary"],
        overall_confidence_score=overall_confidence_score,
    )

    if chart_asset is not None:
        asset_repository = ReportAssetRepository(db)

        await asset_repository.create(
            report_id=report.id,
            asset_type=chart_asset["asset_type"],
            file_path=chart_asset["file_path"],
            caption=chart_asset["caption"],
        )

    evidence_repository = EvidenceRepository(db)
    evidence = await evidence_repository.list_for_research_run(run.id)

    sources = await SourceRepository(db).list_for_research_run(run.id)

    evidence_by_id = {
        evidence_item.id: evidence_item
        for evidence_item in evidence
    }
    source_position_by_id = {
        source.id: index + 1
        for index, source in enumerate(sources)
    }

    citation_repository = CitationRepository(db)
    created_citation_keys: set[tuple[uuid.UUID, uuid.UUID]] = set()

    # Build mapping from persisted source.id -> selected-report position (1..N)
    from app.domain.services.report_source_selection import (
        _normalized_source_url,
        select_report_sources,
    )

    report_sources = result.get("verified_sources") or result.get("sources") or []
    selected_report_sources = select_report_sources(report_sources)

    persisted_by_normalized_url: dict[str, object] = {}
    for src in sources:
        norm = _normalized_source_url({"url": src.url})
        if norm:
            persisted_by_normalized_url[norm] = src

    selected_position_by_source_id: dict[uuid.UUID, int] = {}
    for idx, sel in enumerate(selected_report_sources, start=1):
        norm = _normalized_source_url(sel)
        persisted = persisted_by_normalized_url.get(norm)
        if persisted:
            selected_position_by_source_id[persisted.id] = idx

    for claim in claims:
        for evidence_id in claim.supporting_evidence_ids or []:
            evidence_item = evidence_by_id.get(
                uuid.UUID(evidence_id),
            )

            if evidence_item is None:
                continue

            global_position = source_position_by_id.get(
                evidence_item.source_id,
            )

            selected_position = selected_position_by_source_id.get(
                evidence_item.source_id
            )

            # Accept if either the global persisted position or the report-local
            # selected position appears in the report's referenced markers.
            referenced = referenced_source_positions
            matches_global = (
                global_position is not None and global_position in referenced
            )
            matches_selected = (
                selected_position is not None and selected_position in referenced
            )

            if not (matches_global or matches_selected):
                continue

            citation_key = (claim.id, evidence_item.source_id)

            if citation_key in created_citation_keys:
                continue

            created_citation_keys.add(citation_key)

            # Prefer the marker that actually appears in the report.
            if matches_global:
                marker_num = global_position
            else:
                marker_num = selected_position

            await citation_repository.create(
                report_id=report.id,
                claim_id=claim.id,
                source_id=evidence_item.source_id,
                inline_marker=f"[Source {marker_num}]",
            )


async def persist_evaluation_results(
    db: AsyncSession,
    run: ResearchRun,
    result: dict,
) -> None:
    """Persist evaluation rows once per research run."""

    evaluation_items = list(result.get("evaluations") or [])
    report_data = result.get("report") or {}

    if not any(
        item.get("dimension") == "report_quality"
        for item in evaluation_items
    ):
        report_markdown = report_data.get("content_markdown", "")
        executive_summary = report_data.get("executive_summary")
        report_quality = calculate_report_quality(
            report_markdown=report_markdown,
            executive_summary=executive_summary,
        )

        evaluation_items.append(
            {
                "dimension": "report_quality",
                "score": report_quality["score"],
                "details": report_quality,
            }
        )

    if not evaluation_items:
        return

    repository = EvaluationRepository(db)
    existing = await repository.list_for_research_run(run.id)

    if existing:
        return

    for item in evaluation_items:
        await repository.create(
            research_run_id=run.id,
            dimension=item["dimension"],
            score=item["score"],
            details=item.get("details") or {},
        )
