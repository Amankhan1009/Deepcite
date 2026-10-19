from app.application.use_cases.persist_research_result import (
    _referenced_source_positions,
)


def test_referenced_source_positions_extracts_unique_markers():
    positions = _referenced_source_positions(
        """
Finding one [Source 1].
Finding two [Source 3].
Finding three (Source 8).
Another claim [Source 1].
"""
    )

    assert positions == {1, 3, 8}


def test_referenced_source_positions_ignores_invalid_markers():
    positions = _referenced_source_positions(
        "Unrelated content [source x]."
    )

    assert positions == set()


def test_referenced_source_positions_handles_compound_and_multiple_markers():
    positions = _referenced_source_positions(
        """
Finding combined [Sources 1, 2].
Another combined [Source 3, 4].
Adjacent [Source 5][Source 6].
"""
    )

    assert positions == {1, 2, 3, 4, 5, 6}