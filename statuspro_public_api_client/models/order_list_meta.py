from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="OrderListMeta")


@_attrs_define
class OrderListMeta:
    current_page: int | Unset = UNSET
    from_: int | None | Unset = UNSET
    last_page: int | Unset = UNSET
    per_page: int | Unset = UNSET
    to: int | None | Unset = UNSET
    total: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        current_page = self.current_page

        from_: int | None | Unset
        if isinstance(self.from_, Unset):
            from_ = UNSET
        else:
            from_ = self.from_

        last_page = self.last_page

        per_page = self.per_page

        to: int | None | Unset
        if isinstance(self.to, Unset):
            to = UNSET
        else:
            to = self.to

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if current_page is not UNSET:
            field_dict["current_page"] = current_page
        if from_ is not UNSET:
            field_dict["from"] = from_
        if last_page is not UNSET:
            field_dict["last_page"] = last_page
        if per_page is not UNSET:
            field_dict["per_page"] = per_page
        if to is not UNSET:
            field_dict["to"] = to
        if total is not UNSET:
            field_dict["total"] = total

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        current_page = d.pop("current_page", UNSET)

        def _parse_from_(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        from_ = _parse_from_(d.pop("from", UNSET))

        last_page = d.pop("last_page", UNSET)

        per_page = d.pop("per_page", UNSET)

        def _parse_to(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        to = _parse_to(d.pop("to", UNSET))

        total = d.pop("total", UNSET)

        order_list_meta = cls(
            current_page=current_page,
            from_=from_,
            last_page=last_page,
            per_page=per_page,
            to=to,
            total=total,
        )

        order_list_meta.additional_properties = d
        return order_list_meta

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
