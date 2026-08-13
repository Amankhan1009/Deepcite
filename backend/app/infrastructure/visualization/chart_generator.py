from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from app.infrastructure.llm.groq_client import ChartSpec


def render_chart(
    spec: ChartSpec,
    output_path: Path,
) -> Path:
    """Render a validated chart specification as a PNG file."""

    if len(spec.labels) != len(spec.values):
        raise ValueError("Chart labels and values must have the same length")

    if not spec.labels:
        raise ValueError("Chart data cannot be empty")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(10, 6))

    if spec.chart_type == "bar":
        axis.bar(spec.labels, spec.values)
        axis.tick_params(axis="x", rotation=30)

    elif spec.chart_type == "line":
        axis.plot(
            spec.labels,
            spec.values,
            marker="o",
            linewidth=2,
        )
        axis.tick_params(axis="x", rotation=30)

    elif spec.chart_type == "table":
        axis.axis("off")
        axis.table(
            cellText=[
                [label, value]
                for label, value in zip(
                    spec.labels,
                    spec.values,
                    strict=True,
                )
            ],
            colLabels=["Label", "Value"],
            loc="center",
        )

    else:
        raise ValueError(
            f"Unsupported chart type: {spec.chart_type}"
        )

    axis.set_title(spec.title)
    figure.tight_layout()
    figure.savefig(output_path, format="png", dpi=150)
    plt.close(figure)

    return output_path