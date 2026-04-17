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

T = TypeVar("T", bound="BulkStatusUpdateRequest")


@_attrs_define
class BulkStatusUpdateRequest:
    order_ids: list[int]
    status_code: str
    comment: str | Unset = UNSET
    public: bool | Unset = False
    email_customer: bool | Unset = True
    email_additional: bool | Unset = True
    send_at: int | Unset = UNSET
    due_date: datetime.date | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        order_ids = self.order_ids

        status_code = self.status_code

        comment = self.comment

        public = self.public

        email_customer = self.email_customer

        email_additional = self.email_additional

        send_at = self.send_at

        due_date: str | Unset = UNSET
        if not isinstance(self.due_date, Unset):
            due_date = self.due_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "order_ids": order_ids,
                "status_code": status_code,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if public is not UNSET:
            field_dict["public"] = public
        if email_customer is not UNSET:
            field_dict["email_customer"] = email_customer
        if email_additional is not UNSET:
            field_dict["email_additional"] = email_additional
        if send_at is not UNSET:
            field_dict["send_at"] = send_at
        if due_date is not UNSET:
            field_dict["due_date"] = due_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        order_ids = cast(list[int], d.pop("order_ids"))

        status_code = d.pop("status_code")

        comment = d.pop("comment", UNSET)

        public = d.pop("public", UNSET)

        email_customer = d.pop("email_customer", UNSET)

        email_additional = d.pop("email_additional", UNSET)

        send_at = d.pop("send_at", UNSET)

        _due_date = d.pop("due_date", UNSET)
        due_date: datetime.date | Unset
        if isinstance(_due_date, Unset):
            due_date = UNSET
        else:
            due_date = isoparse(_due_date).date()

        bulk_status_update_request = cls(
            order_ids=order_ids,
            status_code=status_code,
            comment=comment,
            public=public,
            email_customer=email_customer,
            email_additional=email_additional,
            send_at=send_at,
            due_date=due_date,
        )

        bulk_status_update_request.additional_properties = d
        return bulk_status_update_request

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
