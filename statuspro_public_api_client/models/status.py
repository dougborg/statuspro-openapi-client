from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.status_translations import StatusTranslations


T = TypeVar("T", bound="Status")


@_attrs_define
class Status:
    is_set: bool | Unset = UNSET
    code: str | Unset = UNSET
    name: str | Unset = UNSET
    public_name: None | str | Unset = UNSET
    description: str | Unset = UNSET
    public: bool | Unset = UNSET
    set_at: datetime.datetime | None | Unset = UNSET
    auto_change_at: datetime.datetime | None | Unset = UNSET
    translations: StatusTranslations | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_set = self.is_set

        code = self.code

        name = self.name

        public_name: None | str | Unset
        if isinstance(self.public_name, Unset):
            public_name = UNSET
        else:
            public_name = self.public_name

        description = self.description

        public = self.public

        set_at: None | str | Unset
        if isinstance(self.set_at, Unset):
            set_at = UNSET
        elif isinstance(self.set_at, datetime.datetime):
            set_at = self.set_at.isoformat()
        else:
            set_at = self.set_at

        auto_change_at: None | str | Unset
        if isinstance(self.auto_change_at, Unset):
            auto_change_at = UNSET
        elif isinstance(self.auto_change_at, datetime.datetime):
            auto_change_at = self.auto_change_at.isoformat()
        else:
            auto_change_at = self.auto_change_at

        translations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.translations, Unset):
            translations = self.translations.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_set is not UNSET:
            field_dict["is_set"] = is_set
        if code is not UNSET:
            field_dict["code"] = code
        if name is not UNSET:
            field_dict["name"] = name
        if public_name is not UNSET:
            field_dict["public_name"] = public_name
        if description is not UNSET:
            field_dict["description"] = description
        if public is not UNSET:
            field_dict["public"] = public
        if set_at is not UNSET:
            field_dict["set_at"] = set_at
        if auto_change_at is not UNSET:
            field_dict["auto_change_at"] = auto_change_at
        if translations is not UNSET:
            field_dict["translations"] = translations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.status_translations import StatusTranslations

        d = dict(src_dict)
        is_set = d.pop("is_set", UNSET)

        code = d.pop("code", UNSET)

        name = d.pop("name", UNSET)

        def _parse_public_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        public_name = _parse_public_name(d.pop("public_name", UNSET))

        description = d.pop("description", UNSET)

        public = d.pop("public", UNSET)

        def _parse_set_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                set_at_type_0 = isoparse(data)

                return set_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        set_at = _parse_set_at(d.pop("set_at", UNSET))

        def _parse_auto_change_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                auto_change_at_type_0 = isoparse(data)

                return auto_change_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        auto_change_at = _parse_auto_change_at(d.pop("auto_change_at", UNSET))

        _translations = d.pop("translations", UNSET)
        translations: StatusTranslations | Unset
        if isinstance(_translations, Unset):
            translations = UNSET
        else:
            translations = StatusTranslations.from_dict(_translations)

        status = cls(
            is_set=is_set,
            code=code,
            name=name,
            public_name=public_name,
            description=description,
            public=public,
            set_at=set_at,
            auto_change_at=auto_change_at,
            translations=translations,
        )

        status.additional_properties = d
        return status

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
