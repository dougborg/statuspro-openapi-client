"""Tests for the structured-content shape of mutation result schemas.

Pins the contract: each result type (StatusChangeResult, CommentResult,
DueDateChangeResult, BulkStatusChangeResult) is only constructed after
the API call has been issued, so ``confirmed`` is always ``True``. There
is no in-band declined path — the host gates user-confirmation via the
``destructiveHint`` annotation, not via a server-side elicitation.

Mirrors the elicitation drop in katana-openapi-client@e49d45e2 (#436).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from statuspro_mcp.tools.schemas import (
    BulkStatusChangeResult,
    CommentResult,
    DueDateChangeResult,
    StatusChangeResult,
)


@pytest.mark.unit
class TestResultSchemasAlwaysConfirmed:
    """Each result schema's ``confirmed`` field is fixed to True. Pinning the
    ``Literal[True]`` type so a regression that loosens it back to plain
    ``bool`` (which would silently allow ``confirmed=False`` to slip through
    again) surfaces here."""

    def test_status_change_result_confirmed_is_true(self):
        result = StatusChangeResult(
            order_id=1, new_status_code="st000003", success=True, http_status=200
        )
        assert result.confirmed is True

    def test_comment_result_confirmed_is_true(self):
        result = CommentResult(order_id=1, success=True, http_status=200)
        assert result.confirmed is True

    def test_due_date_change_result_confirmed_is_true(self):
        result = DueDateChangeResult(
            order_id=1, new_due_date="2026-04-01", success=True, http_status=200
        )
        assert result.confirmed is True

    def test_bulk_status_change_result_confirmed_is_true(self):
        result = BulkStatusChangeResult(
            order_count=10,
            target_status_code="st000003",
            success=True,
            http_status=202,
        )
        assert result.confirmed is True

    def test_status_change_result_rejects_confirmed_false(self):
        """If the field type ever drifts back to ``bool``, this test fails —
        catching the same Copilot-flagged "declined path with confirmed=True"
        regression that motivated the original tightening."""
        with pytest.raises(ValidationError):
            StatusChangeResult(
                confirmed=False,  # type: ignore[arg-type]
                order_id=1,
                new_status_code="st000003",
                success=False,
                http_status=0,
            )
