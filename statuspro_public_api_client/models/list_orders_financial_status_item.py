from enum import StrEnum


class ListOrdersFinancialStatusItem(StrEnum):
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    PENDING = "pending"
    REFUNDED = "refunded"
    UNPAID = "unpaid"
    VOIDED = "voided"

    def __str__(self) -> str:
        return str(self.value)
