"""Tests for the structured-content shape of mutation result schemas.

Pins the contract that the four result types (StatusChangeResult,
CommentResult, DueDateChangeResult, BulkStatusChangeResult) accept
``confirmed=False`` for the user-declined path. Before the fix in
PR #46 follow-up, these all hard-coded ``confirmed: Literal[True]``,
which made structured output claim the action was confirmed even when
the user declined — misleading for downstream consumers.
"""

from __future__ import annotations

import pytest
from statuspro_mcp.tools.schemas import (
    BulkStatusChangeResult,
    CommentResult,
    DueDateChangeResult,
    StatusChangeResult,
)


@pytest.mark.unit
class TestResultSchemasAcceptDeclinedConfirmation:
    """Each result schema must accept confirmed=False so the declined
    elicitation path can be represented accurately in structured output.
    """

    def test_status_change_result_default_confirmed_true(self):
        """The success path defaults to confirmed=True (backwards compatible)."""
        result = StatusChangeResult(
            order_id=1, new_status_code="st000003", success=True, http_status=200
        )
        assert result.confirmed is True

    def test_status_change_result_declined_path(self):
        """Declined elicitation surfaces confirmed=False alongside success=False."""
        result = StatusChangeResult(
            confirmed=False,
            order_id=1,
            new_status_code="st000003",
            success=False,
            http_status=0,
            message="User declined",
        )
        assert result.confirmed is False
        assert result.success is False

    def test_comment_result_declined_path(self):
        result = CommentResult(
            confirmed=False,
            order_id=1,
            success=False,
            http_status=0,
            message="User cancelled",
        )
        assert result.confirmed is False

    def test_due_date_change_result_declined_path(self):
        result = DueDateChangeResult(
            confirmed=False,
            order_id=1,
            new_due_date="2026-04-01",
            success=False,
            http_status=0,
            message="User declined",
        )
        assert result.confirmed is False

    def test_bulk_status_change_result_declined_path(self):
        result = BulkStatusChangeResult(
            confirmed=False,
            order_count=10,
            target_status_code="st000003",
            success=False,
            http_status=0,
            message="User cancelled",
        )
        assert result.confirmed is False
