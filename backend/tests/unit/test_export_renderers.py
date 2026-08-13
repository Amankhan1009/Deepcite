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