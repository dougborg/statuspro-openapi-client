"""Tests for the list-coercion BeforeValidator.

LLM-emitted call shapes that motivated this — both observed in the wild
during katana-openapi-client's #428 incident:

  CSV form:           ``order_ids='20486,20487,20488'``
  JSON-stringified:   ``order_ids='[20486, 20487, 20488]'``

Pydantic raises ``Input should be a valid list [type=list_type,
input_type=str]`` for both, the tool call aborts, and the user has to
retry. With the BeforeValidator wired in via the ``Coerced*`` aliases,
both shapes recover transparently without losing data.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field, ValidationError
from statuspro_mcp.tools.list_coercion import (
    CoercedIntListOpt,
    CoercedStrIntList,
    CoercedStrListOpt,
)


class _RequestStub(BaseModel):
    """Mimics the shape of an LLM-facing tool parameter / request-model field."""

    tags: CoercedStrListOpt = Field(default=None)
    order_ids: CoercedIntListOpt = Field(default=None)
    # Stub of a ``CoercedStrIntList`` (mixed str|int list, required-typed)
    # so the mixed-type tests below can exercise the alias. Uses
    # ``default_factory`` so ``_build()`` can omit it.
    required_mixed: CoercedStrIntList = Field(default_factory=list)


def _build(**kwargs: object) -> _RequestStub:
    """Use ``model_validate`` so we can pass string-typed inputs through the
    BeforeValidator without arguing with pyright about the field annotation.
    Mirrors how MCP/fastmcp actually constructs the request from the LLM-supplied
    JSON dict."""
    return _RequestStub.model_validate(kwargs)


def test_list_input_passes_through_unchanged():
    assert _build(tags=["A", "B", "C"]).tags == ["A", "B", "C"]


def test_csv_string_splits_into_list():
    assert _build(tags="rush,priority,vip").tags == ["rush", "priority", "vip"]


def test_csv_string_strips_whitespace_and_drops_empty_fragments():
    assert _build(tags=" rush , , priority ,").tags == ["rush", "priority"]


def test_json_stringified_array_is_parsed():
    assert _build(tags='["rush", "priority"]').tags == ["rush", "priority"]


def test_json_stringified_array_with_ints_coerces_for_int_field():
    assert _build(order_ids="[20486, 20487, 20488]").order_ids == [
        20486,
        20487,
        20488,
    ]


def test_csv_string_of_ints_coerces_via_pydantic():
    # CSV path returns strings; pydantic's list[int] coerces each element.
    assert _build(order_ids="20486,20487,20488").order_ids == [20486, 20487, 20488]


def test_empty_string_yields_empty_list():
    assert _build(tags="").tags == []


def test_whitespace_only_string_yields_empty_list():
    assert _build(tags="   ").tags == []


def test_none_passes_through():
    assert _build(tags=None).tags is None


def test_omitted_field_keeps_default():
    assert _build().tags is None


def test_malformed_json_falls_back_to_csv_split():
    # Unclosed bracket — JSON parse fails, CSV split runs on the whole string.
    assert _build(tags="[rush,priority").tags == ["[rush", "priority"]


def test_non_list_json_falls_back_to_csv_split():
    # JSON parses but isn't a list — keep the string-y CSV path.
    assert _build(tags='{"key":"value"}').tags == ['{"key":"value"}']


def test_non_string_non_list_input_raises_normal_pydantic_error():
    # Don't mask genuinely wrong types — pydantic's diagnostic still fires.
    with pytest.raises(ValidationError):
        _build(tags=42)


def test_int_input_for_int_list_raises_normal_pydantic_error():
    # Same — a bare int for list[int] should still be a real error.
    with pytest.raises(ValidationError):
        _build(order_ids=42)


def test_single_value_string_no_comma_yields_one_item_list():
    # ``tags="rush"`` is the LLM's most innocent form of the bug.
    assert _build(tags="rush").tags == ["rush"]


def test_mixed_type_list_passthrough():
    # The CoercedStrIntList alias accepts mixed input types — pydantic
    # validates each element against ``str | int``.
    req = _build(required_mixed=["rush", 12345, "vip"])
    assert req.required_mixed == ["rush", 12345, "vip"]


def test_csv_with_numeric_items_for_str_int_list_keeps_strings():
    # CSV path returns strings; pydantic's ``str | int`` union accepts both.
    req = _build(required_mixed="rush,12345")
    assert req.required_mixed == ["rush", "12345"]


def test_empty_string_plus_min_length_one_raises_min_length_error():
    """Empty string coerces to ``[]``, so a field with ``min_length=1``
    raises a ``too_short`` error rather than the original ``list_type``
    error. Documents the resulting UX so a future contributor doesn't
    accidentally regress to the old shape.
    """

    class _Req(BaseModel):
        tags: CoercedStrListOpt = Field(default=None, min_length=1)

    with pytest.raises(ValidationError) as exc_info:
        _Req.model_validate({"tags": ""})

    errors = exc_info.value.errors()
    assert errors[0]["type"] == "too_short"


def test_non_numeric_string_for_int_list_raises_pydantic_error():
    # CSV split yields ``["abc"]``; pydantic can't coerce that to int.
    with pytest.raises(ValidationError) as exc_info:
        _build(order_ids="abc")
    errors = exc_info.value.errors()
    assert errors[0]["type"] == "int_parsing"
