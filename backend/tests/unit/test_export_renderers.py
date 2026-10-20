from types import SimpleNamespace

from app.application.use_cases.export_report import ExportableReport
from app.infrastructure.export.renderers import render_report_export


def _exportable_report() -> ExportableReport:
    report = SimpleNamespace(
        content_markdown=(
            "# Retrieval-Augmented Generation\n\n"
            "Retrieval improves factual accuracy."
        ),
        executive_summary="Retrieval provides relevant external context.",
    )

    return ExportableReport(
        report=report,
        assets=[],
    )


def test_markdown_export_contains_report_content():
    content, media_type, extension = render_report_export(
        _exportable_report(),
        "markdown",
    )

    assert media_type.startswith("text/markdown")
    assert extension == "md"
    assert b"Retrieval-Augmented Generation" in content
    assert b"factual accuracy" in content


def test_pdf_export_returns_pdf_bytes():
    content, media_type, extension = render_report_export(
        _exportable_report(),
        "pdf",
    )

    assert media_type == "application/pdf"
    assert extension == "pdf"
    assert content.startswith(b"%PDF")


def test_docx_export_returns_docx_bytes():
    content, media_type, extension = render_report_export(
        _exportable_report(),
        "docx",
    )

    assert (
        media_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert extension == "docx"
    assert content.startswith(b"PK")


def test_markdown_export_renumbers_gap_citations_sequentially():
    report = SimpleNamespace(
        content_markdown=(
            "# Evidence Grounding\n\n"
            "Speculative decoding reduces latency [Source 2]. "
            "Medusa scales memory [Source 4]."
        ),
        executive_summary="Summary of findings [Source 2].",
    )
    citations = [
        {
            "source_id": "src-1",
            "inline_marker": "[Source 2]",
            "source_title": "Speculative Decoding Paper",
            "source_url": "https://arxiv.org/abs/2211.17192",
        },
        {
            "source_id": "src-2",
            "inline_marker": "[Source 4]",
            "source_title": "Medusa Paper",
            "source_url": "https://arxiv.org/abs/2301.12345",
        },
    ]

    exportable = ExportableReport(
        report=report,
        assets=[],
        citations=citations,
    )

    content, media_type, extension = render_report_export(exportable, "markdown")
    text = content.decode("utf-8")

    assert "[Source 1]" in text
    assert "[Source 2]" in text
    assert "[Source 4]" not in text
    assert "## References" in text
    assert "[Source 1] Speculative Decoding Paper" in text
    assert "[Source 2] Medusa Paper" in text
