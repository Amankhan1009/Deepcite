from pathlib import Path

from app.infrastructure.llm.groq_client import ChartSpec
from app.infrastructure.visualization.chart_generator import render_chart


def test_render_chart_creates_valid_png(tmp_path: Path):
    output_path = tmp_path / "chart.png"

    spec = ChartSpec(
        chart_type="bar",
        title="Production AI Risks",
        labels=["Security", "Reliability", "Privacy"],
        values=[8.0, 7.0, 6.0],
        source_claim_ids=[0, 1, 2],
    )

    rendered_path = render_chart(
        spec=spec,
        output_path=output_path,
    )

    assert rendered_path == output_path
    assert rendered_path.exists()
    assert rendered_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"