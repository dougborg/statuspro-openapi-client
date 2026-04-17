from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateOrderStatusRequest")


@_attrs_define
class UpdateOrderStatusRequest:
    status_code: str
    comment: str | Unset = UNSET
    public: bool | Unset = False
    email_customer: bool | Unset = True
    email_additional: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status_code = self.status_code

        comment = self.comment

        public = self.public

        email_customer = self.email_customer

        email_additional = self.email_additional

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status_code = d.pop("status_code")

        comment = d.pop("comment", UNSET)

        public = d.pop("public", UNSET)

        email_customer = d.pop("email_customer", UNSET)

        email_additional = d.pop("email_additional", UNSET)

        update_order_status_request = cls(
            status_code=status_code,
            comment=comment,
            public=public,
            email_customer=email_customer,
            email_additional=email_additional,
        )

        update_order_status_request.additional_properties = d
        return update_order_status_request

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
