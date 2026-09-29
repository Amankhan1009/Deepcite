import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.claim_repository import ClaimRepository
from app.infrastructure.db.repositories.evidence_repository import EvidenceRepository
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.db.repositories.source_repository import SourceRepository


class ResearchRunNotFoundError(Exception):
    """Raised when a research run is missing or not owned by the user."""


async def get_research_evidence(
    db: AsyncSession,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[dict]:
    """Retrieve verified research evidence items for a research run."""

    run_repository = ResearchRunRepository(db)
    run = await run_repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if run is None or run.deleted_at is not None:
        raise ResearchRunNotFoundError

    source_repository = SourceRepository(db)
    evidence_repository = EvidenceRepository(db)
    claim_repository = ClaimRepository(db)

    sources = await source_repository.list_for_research_run(research_run_id)
    evidence_items = await evidence_repository.list_for_research_run(research_run_id)
    claims = await claim_repository.list_for_research_run(research_run_id)

    source_by_id = {source.id: source for source in sources}
    evidence_by_id = {evidence.id: evidence for evidence in evidence_items}

    used_evidence_ids: set[uuid.UUID] = set()
    used_source_ids: set[uuid.UUID] = set()
    items: list[dict] = []

    if claims:
        for claim in claims:
            supporting_ids = claim.supporting_evidence_ids or []
            if supporting_ids:
                for ev_id_str in supporting_ids:
                    try:
                        ev_uuid = uuid.UUID(ev_id_str)
                    except (ValueError, TypeError):
                        continue

                    ev = evidence_by_id.get(ev_uuid)
                    if ev is not None:
                        used_evidence_ids.add(ev.id)
                        src = source_by_id.get(ev.source_id)
                        if src is not None:
                            used_source_ids.add(src.id)

                        items.append(
                            {
                                "id": f"{claim.id}_{ev.id}",
                                "source_id": src.id if src else None,
                                "source_title": src.title if src else None,
                                "source_url": src.url if src else "",
                                "source_reliability_score": (
                                    float(src.reliability_score)
                                    if src and src.reliability_score is not None
                                    else None
                                ),
                                "claim_text": claim.text,
                                "supporting_evidence": ev.claim_text,
                                "verification_status": claim.fact_check_status,
                                "confidence_score": (
                                    float(claim.confidence_score)
                                    if claim.confidence_score is not None
                                    else None
                                ),
                            }
                        )
            else:
                items.append(
                    {
                        "id": str(claim.id),
                        "source_id": None,
                        "source_title": None,
                        "source_url": "",
                        "source_reliability_score": None,
                        "claim_text": claim.text,
                        "supporting_evidence": None,
                        "verification_status": claim.fact_check_status,
                        "confidence_score": (
                            float(claim.confidence_score)
                            if claim.confidence_score is not None
                            else None
                        ),
                    }
                )

    for ev in evidence_items:
        if ev.id not in used_evidence_ids:
            used_evidence_ids.add(ev.id)
            src = source_by_id.get(ev.source_id)
            if src is not None:
                used_source_ids.add(src.id)

            items.append(
                {
                    "id": str(ev.id),
                    "source_id": src.id if src else None,
                    "source_title": src.title if src else None,
                    "source_url": src.url if src else "",
                    "source_reliability_score": (
                        float(src.reliability_score)
                        if src and src.reliability_score is not None
                        else None
                    ),
                    "claim_text": ev.claim_text,
                    "supporting_evidence": (
                        src.raw_content_ref if src else None
                    ) or ev.claim_text,
                    "verification_status": (
                        "verified"
                        if src and src.reliability_score and src.reliability_score >= 0.5
                        else "unverified"
                    ),
                    "confidence_score": (
                        float(src.reliability_score)
                        if src and src.reliability_score is not None
                        else None
                    ),
                }
            )

    for src in sources:
        if src.id not in used_source_ids:
            items.append(
                {
                    "id": str(src.id),
                    "source_id": src.id,
                    "source_title": src.title,
                    "source_url": src.url,
                    "source_reliability_score": (
                        float(src.reliability_score)
                        if src.reliability_score is not None
                        else None
                    ),
                    "claim_text": src.title or src.url,
                    "supporting_evidence": src.raw_content_ref,
                    "verification_status": (
                        "verified"
                        if src.reliability_score and src.reliability_score >= 0.5
                        else "unverified"
                    ),
                    "confidence_score": (
                        float(src.reliability_score)
                        if src.reliability_score is not None
                        else None
                    ),
                }
            )

    if not items:
        try:
            from app.infrastructure.agents.checkpointer import get_checkpointer

            async with get_checkpointer() as checkpointer:
                config = {"configurable": {"thread_id": str(research_run_id)}}
                checkpoint_tuple = await checkpointer.aget_tuple(config)
                if checkpoint_tuple and checkpoint_tuple.checkpoint:
                    channel_values = checkpoint_tuple.checkpoint.get(
                        "channel_values", {}
                    )
                    state_sources = (
                        channel_values.get("verified_sources")
                        or channel_values.get("sources")
                        or []
                    )
                    state_evidence = channel_values.get("evidence") or []
                    reasoning_data = channel_values.get("reasoning") or {}
                    reasoning_items = reasoning_data.get("items") or []
                    fact_checks_data = channel_values.get("fact_checks") or {}
                    fact_check_items = fact_checks_data.get("items") or []

                    src_by_idx = {
                        s.get("source_index", idx): s
                        for idx, s in enumerate(state_sources)
                    }
                    ev_by_idx = {
                        idx: ev for idx, ev in enumerate(state_evidence)
                    }

                    fact_check_map = {
                        fc.get("claim_index"): fc for fc in fact_check_items
                    }

                    if reasoning_items:
                        for claim_idx, claim_text in enumerate(reasoning_items):
                            fc = fact_check_map.get(claim_idx, {})
                            supp_ev_indices = (
                                fc.get("supporting_evidence_indexes") or []
                            )
                            if supp_ev_indices:
                                for ev_idx in supp_ev_indices:
                                    ev = ev_by_idx.get(ev_idx, {})
                                    src_idx = ev.get("source_index")
                                    src = src_by_idx.get(src_idx, {})
                                    items.append(
                                        {
                                            "id": f"state_{claim_idx}_{ev_idx}",
                                            "source_id": None,
                                            "source_title": src.get("title"),
                                            "source_url": src.get("url", ""),
                                            "source_reliability_score": src.get(
                                                "reliability_score"
                                            ),
                                            "claim_text": claim_text,
                                            "supporting_evidence": ev.get(
                                                "claim_text"
                                            ),
                                            "verification_status": fc.get(
                                                "status", "verified"
                                            ),
                                            "confidence_score": src.get(
                                                "reliability_score"
                                            ),
                                        }
                                    )
                            else:
                                items.append(
                                    {
                                        "id": f"state_claim_{claim_idx}",
                                        "source_id": None,
                                        "source_title": None,
                                        "source_url": "",
                                        "source_reliability_score": None,
                                        "claim_text": claim_text,
                                        "supporting_evidence": None,
                                        "verification_status": fc.get(
                                            "status", "unverified"
                                        ),
                                        "confidence_score": None,
                                    }
                                )

                    if not items and state_sources:
                        for idx, s in enumerate(state_sources):
                            items.append(
                                {
                                    "id": f"state_src_{idx}",
                                    "source_id": None,
                                    "source_title": s.get("title"),
                                    "source_url": s.get("url", ""),
                                    "source_reliability_score": s.get(
                                        "reliability_score"
                                    ),
                                    "claim_text": s.get("title")
                                    or s.get("url"),
                                    "supporting_evidence": s.get("content"),
                                    "verification_status": (
                                        "verified"
                                        if s.get("reliability_score")
                                        and s.get("reliability_score") >= 0.5
                                        else "unverified"
                                    ),
                                    "confidence_score": s.get(
                                        "reliability_score"
                                    ),
                                }
                            )
        except Exception:
            pass

    return items
