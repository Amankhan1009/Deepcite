from app.infrastructure.evaluation import evaluator


async def test_evaluate_research_returns_available_dimensions(
    monkeypatch,
):
    async def fake_generate_evaluation(**kwargs):
        return type(
            "Evaluation",
            (),
            {
                "planning_quality_score": 0.9,
                "planning_quality_rationale": "Focused plan.",
                "search_quality_score": 0.8,
                "search_quality_rationale": "Relevant sources.",
            },
        )()

    async def fake_generate_quality_evaluation(**kwargs):
        return type(
            "QualityEvaluation",
            (),
            {
                "groundedness_score": 0.85,
                "groundedness_rationale": "Evidence supports the report.",
                "hallucination_detection_score": 0.9,
                "hallucination_detection_rationale": (
                    "No major unsupported statements."
                ),
                "unsupported_statements": [],
            },
        )()

    monkeypatch.setattr(
        evaluator,
        "generate_evaluation",
        fake_generate_evaluation,
    )
    monkeypatch.setattr(
        evaluator,
        "generate_quality_evaluation",
        fake_generate_quality_evaluation,
    )

    evaluations = await evaluator.evaluate_research(
        question="What are AI risks?",
        plan={"sub_questions": ["Risks"]},
        sources=[{"reliability_score": 0.85}],
        report={
            "executive_summary": "AI risk research summary.",
            "content_markdown": (
                "# Report\n\n"
                "AI creates risks [Source 1]."
            ),
        },
        evidence=[
            {
                "claim_text": "AI creates risks.",
                "source_index": 0,
            }
        ],
        reasoning=[{"claim_text": "AI creates risks."}],
        fact_checks=[{"status": "supported"}],
    )

    evaluations_by_dimension = {
        item["dimension"]: item
        for item in evaluations
    }

    assert evaluations_by_dimension["planning_quality"]["score"] == 0.9
    assert evaluations_by_dimension["search_quality"]["score"] == 0.8
    assert evaluations_by_dimension["source_reliability"]["score"] == 0.85
    assert evaluations_by_dimension["citation_coverage"]["score"] == 1.0
    assert evaluations_by_dimension["report_quality"]["score"] is not None
    assert (
        evaluations_by_dimension["report_quality"]["details"][
            "executive_summary_present"
        ]
        is True
    )
    assert evaluations_by_dimension["groundedness"]["score"] == 0.85
    assert (
        evaluations_by_dimension["hallucination_detection"]["score"]
        == 0.9
    )
    assert evaluations_by_dimension["overall"]["score"] is not None


async def test_evaluate_research_persists_deterministic_scores_when_judge_fails(
    monkeypatch,
):
    async def fake_generate_evaluation(**kwargs):
        return type(
            "Evaluation",
            (),
            {
                "planning_quality_score": 0.9,
                "planning_quality_rationale": "Focused plan.",
                "search_quality_score": 0.8,
                "search_quality_rationale": "Relevant sources.",
            },
        )()

    async def failing_generate_quality_evaluation(**kwargs):
        raise RuntimeError("Groq request payload exceeded its limit")

    monkeypatch.setattr(
        evaluator,
        "generate_evaluation",
        fake_generate_evaluation,
    )
    monkeypatch.setattr(
        evaluator,
        "generate_quality_evaluation",
        failing_generate_quality_evaluation,
    )

    evaluations = await evaluator.evaluate_research(
        question="What are AI risks?",
        plan={"sub_questions": ["Risks"]},
        sources=[{"reliability_score": 0.85}],
        report={
            "executive_summary": "AI risk research summary.",
            "content_markdown": (
                "# Report\n\n"
                "AI creates risks [Source 1]."
            ),
        },
        evidence=[
            {
                "claim_text": "AI creates risks.",
                "source_index": 0,
            }
        ],
        reasoning=[{"claim_text": "AI creates risks."}],
        fact_checks=[{"status": "supported"}],
    )

    dimensions = {
        item["dimension"]
        for item in evaluations
    }

    assert "planning_quality" in dimensions
    assert "search_quality" in dimensions
    assert "source_reliability" in dimensions
    assert "citation_coverage" in dimensions
    assert "report_quality" in dimensions
    assert "overall" in dimensions
    assert "groundedness" not in dimensions
    assert "hallucination_detection" not in dimensions