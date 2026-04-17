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
    from ..models.customer import Customer
    from ..models.history_item import HistoryItem
    from ..models.progress_timeline_item import ProgressTimelineItem
    from ..models.status import Status


T = TypeVar("T", bound="OrderResponse")


@_attrs_define
class OrderResponse:
    id: int | Unset = UNSET
    name: str | Unset = UNSET
    order_number: str | Unset = UNSET
    customer: Customer | Unset = UNSET
    status: Status | Unset = UNSET
    history: list[HistoryItem] | Unset = UNSET
    public_progress_timeline: list[ProgressTimelineItem] | Unset = UNSET
    due_date: datetime.datetime | None | Unset = UNSET
    due_date_to: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        order_number = self.order_number

        customer: dict[str, Any] | Unset = UNSET
        if not isinstance(self.customer, Unset):
            customer = self.customer.to_dict()

        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        history: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.history, Unset):
            history = []
            for history_item_data in self.history:
                history_item = history_item_data.to_dict()
                history.append(history_item)

        public_progress_timeline: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.public_progress_timeline, Unset):
            public_progress_timeline = []
            for public_progress_timeline_item_data in self.public_progress_timeline:
                public_progress_timeline_item = (
                    public_progress_timeline_item_data.to_dict()
                )
                public_progress_timeline.append(public_progress_timeline_item)

        due_date: None | str | Unset
        if isinstance(self.due_date, Unset):
            due_date = UNSET
        elif isinstance(self.due_date, datetime.datetime):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        due_date_to: None | str | Unset
        if isinstance(self.due_date_to, Unset):
            due_date_to = UNSET
        elif isinstance(self.due_date_to, datetime.datetime):
            due_date_to = self.due_date_to.isoformat()
        else:
            due_date_to = self.due_date_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if order_number is not UNSET:
            field_dict["order_number"] = order_number
        if customer is not UNSET:
            field_dict["customer"] = customer
        if status is not UNSET:
            field_dict["status"] = status
        if history is not UNSET:
            field_dict["history"] = history
        if public_progress_timeline is not UNSET:
            field_dict["public_progress_timeline"] = public_progress_timeline
        if due_date is not UNSET:
            field_dict["due_date"] = due_date
        if due_date_to is not UNSET:
            field_dict["due_date_to"] = due_date_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer import Customer
        from ..models.history_item import HistoryItem
        from ..models.progress_timeline_item import ProgressTimelineItem
        from ..models.status import Status

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        order_number = d.pop("order_number", UNSET)

        _customer = d.pop("customer", UNSET)
        customer: Customer | Unset
        if isinstance(_customer, Unset):
            customer = UNSET
        else:
            customer = Customer.from_dict(_customer)

        _status = d.pop("status", UNSET)
        status: Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = Status.from_dict(_status)

        _history = d.pop("history", UNSET)
        history: list[HistoryItem] | Unset = UNSET
        if _history is not UNSET:
            history = []
            for history_item_data in _history:
                history_item = HistoryItem.from_dict(history_item_data)

                history.append(history_item)

        _public_progress_timeline = d.pop("public_progress_timeline", UNSET)
        public_progress_timeline: list[ProgressTimelineItem] | Unset = UNSET
        if _public_progress_timeline is not UNSET:
            public_progress_timeline = []
            for public_progress_timeline_item_data in _public_progress_timeline:
                public_progress_timeline_item = ProgressTimelineItem.from_dict(
                    public_progress_timeline_item_data
                )

                public_progress_timeline.append(public_progress_timeline_item)

        def _parse_due_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                due_date_type_0 = isoparse(data)

                return due_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        due_date = _parse_due_date(d.pop("due_date", UNSET))

        def _parse_due_date_to(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                due_date_to_type_0 = isoparse(data)

                return due_date_to_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        due_date_to = _parse_due_date_to(d.pop("due_date_to", UNSET))

        order_response = cls(
            id=id,
            name=name,
            order_number=order_number,
            customer=customer,
            status=status,
            history=history,
            public_progress_timeline=public_progress_timeline,
            due_date=due_date,
            due_date_to=due_date_to,
        )

        order_response.additional_properties = d
        return order_response

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
