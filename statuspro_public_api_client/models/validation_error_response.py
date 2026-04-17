from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.validation_error_response_errors import ValidationErrorResponseErrors


T = TypeVar("T", bound="ValidationErrorResponse")


@_attrs_define
class ValidationErrorResponse:
    message: str | Unset = UNSET
    errors: ValidationErrorResponseErrors | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        errors: dict[str, Any] | Unset = UNSET
        if not isinstance(self.errors, Unset):
            errors = self.errors.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if errors is not UNSET:
            field_dict["errors"] = errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validation_error_response_errors import (
            ValidationErrorResponseErrors,
        )

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _errors = d.pop("errors", UNSET)
        errors: ValidationErrorResponseErrors | Unset
        if isinstance(_errors, Unset):
            errors = UNSET
        else:
            errors = ValidationErrorResponseErrors.from_dict(_errors)

        validation_error_response = cls(
            message=message,
            errors=errors,
        )

        validation_error_response.additional_properties = d
        return validation_error_response

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
