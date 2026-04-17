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
    from ..models.mail_log import MailLog
    from ..models.status import Status


T = TypeVar("T", bound="HistoryItem")


@_attrs_define
class HistoryItem:
    event: str | Unset = UNSET
    status: None | Status | Unset = UNSET
    comment: None | str | Unset = UNSET
    comment_is_public: bool | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    mail_log: MailLog | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.mail_log import MailLog
        from ..models.status import Status

        event = self.event

        status: dict[str, Any] | None | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, Status):
            status = self.status.to_dict()
        else:
            status = self.status

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        comment_is_public = self.comment_is_public

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        mail_log: dict[str, Any] | None | Unset
        if isinstance(self.mail_log, Unset):
            mail_log = UNSET
        elif isinstance(self.mail_log, MailLog):
            mail_log = self.mail_log.to_dict()
        else:
            mail_log = self.mail_log

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if event is not UNSET:
            field_dict["event"] = event
        if status is not UNSET:
            field_dict["status"] = status
        if comment is not UNSET:
            field_dict["comment"] = comment
        if comment_is_public is not UNSET:
            field_dict["comment_is_public"] = comment_is_public
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if mail_log is not UNSET:
            field_dict["mail_log"] = mail_log

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mail_log import MailLog
        from ..models.status import Status

        d = dict(src_dict)
        event = d.pop("event", UNSET)

        def _parse_status(data: object) -> None | Status | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                status_type_0 = Status.from_dict(cast(Mapping[str, Any], data))

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Status | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        comment_is_public = d.pop("comment_is_public", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        def _parse_mail_log(data: object) -> MailLog | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                mail_log_type_0 = MailLog.from_dict(cast(Mapping[str, Any], data))

                return mail_log_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MailLog | None | Unset, data)

        mail_log = _parse_mail_log(d.pop("mail_log", UNSET))

        history_item = cls(
            event=event,
            status=status,
            comment=comment,
            comment_is_public=comment_is_public,
            created_at=created_at,
            mail_log=mail_log,
        )

        history_item.additional_properties = d
        return history_item

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
