from enum import StrEnum


class ListOrdersFulfillmentStatusItem(StrEnum):
    FULFILLED = "fulfilled"
    PARTIAL = "partial"
    RESTOCKED = "restocked"
    UNFULFILLED = "unfulfilled"

    def __str__(self) -> str:
        return str(self.value)
