from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="SetDueDateRequest")


@_attrs_define
class SetDueDateRequest:
    due_date: datetime.date | None
    due_date_to: datetime.date | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        due_date: None | str
        if isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        due_date_to: str | Unset = UNSET
        if not isinstance(self.due_date_to, Unset):
            due_date_to = self.due_date_to.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "due_date": due_date,
            }
        )
        if due_date_to is not UNSET:
            field_dict["due_date_to"] = due_date_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_due_date(data: object) -> datetime.date | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                due_date_type_0 = isoparse(data).date()

                return due_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None, data)

        due_date = _parse_due_date(d.pop("due_date"))

        _due_date_to = d.pop("due_date_to", UNSET)
        due_date_to: datetime.date | Unset
        if isinstance(_due_date_to, Unset):
            due_date_to = UNSET
        else:
            due_date_to = isoparse(_due_date_to).date()

        set_due_date_request = cls(
            due_date=due_date,
            due_date_to=due_date_to,
        )

        set_due_date_request.additional_properties = d
        return set_due_date_request

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
