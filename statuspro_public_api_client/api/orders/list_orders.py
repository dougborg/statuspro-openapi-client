import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.list_orders_financial_status_item import ListOrdersFinancialStatusItem
from ...models.list_orders_fulfillment_status_item import (
    ListOrdersFulfillmentStatusItem,
)
from ...models.order_list_response import OrderListResponse
from ...models.validation_error_response import ValidationErrorResponse


def _get_kwargs(
    *,
    search: str | Unset = UNSET,
    status_code: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    tags_any: list[str] | Unset = UNSET,
    financial_status: list[ListOrdersFinancialStatusItem] | Unset = UNSET,
    fulfillment_status: list[ListOrdersFulfillmentStatusItem] | Unset = UNSET,
    exclude_cancelled: bool | Unset = UNSET,
    due_date_from: datetime.date | Unset = UNSET,
    due_date_to: datetime.date | Unset = UNSET,
    per_page: int | Unset = 15,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["search"] = search

    params["status_code"] = status_code

    json_tags: list[str] | Unset = UNSET
    if not isinstance(tags, Unset):
        json_tags = tags

    params["tags[]"] = json_tags

    json_tags_any: list[str] | Unset = UNSET
    if not isinstance(tags_any, Unset):
        json_tags_any = tags_any

    params["tags_any[]"] = json_tags_any

    json_financial_status: list[str] | Unset = UNSET
    if not isinstance(financial_status, Unset):
        json_financial_status = []
        for financial_status_item_data in financial_status:
            financial_status_item = financial_status_item_data.value
            json_financial_status.append(financial_status_item)

    params["financial_status[]"] = json_financial_status

    json_fulfillment_status: list[str] | Unset = UNSET
    if not isinstance(fulfillment_status, Unset):
        json_fulfillment_status = []
        for fulfillment_status_item_data in fulfillment_status:
            fulfillment_status_item = fulfillment_status_item_data.value
            json_fulfillment_status.append(fulfillment_status_item)

    params["fulfillment_status[]"] = json_fulfillment_status

    params["exclude_cancelled"] = exclude_cancelled

    json_due_date_from: str | Unset = UNSET
    if not isinstance(due_date_from, Unset):
        json_due_date_from = due_date_from.isoformat()
    params["due_date_from"] = json_due_date_from

    json_due_date_to: str | Unset = UNSET
    if not isinstance(due_date_to, Unset):
        json_due_date_to = due_date_to.isoformat()
    params["due_date_to"] = json_due_date_to

    params["per_page"] = per_page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/orders",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | OrderListResponse | ValidationErrorResponse | None:
    if response.status_code == 200:
        response_200 = OrderListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = ValidationErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | OrderListResponse | ValidationErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = UNSET,
    status_code: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    tags_any: list[str] | Unset = UNSET,
    financial_status: list[ListOrdersFinancialStatusItem] | Unset = UNSET,
    fulfillment_status: list[ListOrdersFulfillmentStatusItem] | Unset = UNSET,
    exclude_cancelled: bool | Unset = UNSET,
    due_date_from: datetime.date | Unset = UNSET,
    due_date_to: datetime.date | Unset = UNSET,
    per_page: int | Unset = 15,
) -> Response[ErrorResponse | OrderListResponse | ValidationErrorResponse]:
    """Retrieve a paginated list of orders

     Limited to 60 requests per minute.

    Args:
        search (str | Unset):
        status_code (str | Unset):
        tags (list[str] | Unset):
        tags_any (list[str] | Unset):
        financial_status (list[ListOrdersFinancialStatusItem] | Unset):
        fulfillment_status (list[ListOrdersFulfillmentStatusItem] | Unset):
        exclude_cancelled (bool | Unset):
        due_date_from (datetime.date | Unset):
        due_date_to (datetime.date | Unset):
        per_page (int | Unset):  Default: 15.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | OrderListResponse | ValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        status_code=status_code,
        tags=tags,
        tags_any=tags_any,
        financial_status=financial_status,
        fulfillment_status=fulfillment_status,
        exclude_cancelled=exclude_cancelled,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        per_page=per_page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = UNSET,
    status_code: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    tags_any: list[str] | Unset = UNSET,
    financial_status: list[ListOrdersFinancialStatusItem] | Unset = UNSET,
    fulfillment_status: list[ListOrdersFulfillmentStatusItem] | Unset = UNSET,
    exclude_cancelled: bool | Unset = UNSET,
    due_date_from: datetime.date | Unset = UNSET,
    due_date_to: datetime.date | Unset = UNSET,
    per_page: int | Unset = 15,
) -> ErrorResponse | OrderListResponse | ValidationErrorResponse | None:
    """Retrieve a paginated list of orders

     Limited to 60 requests per minute.

    Args:
        search (str | Unset):
        status_code (str | Unset):
        tags (list[str] | Unset):
        tags_any (list[str] | Unset):
        financial_status (list[ListOrdersFinancialStatusItem] | Unset):
        fulfillment_status (list[ListOrdersFulfillmentStatusItem] | Unset):
        exclude_cancelled (bool | Unset):
        due_date_from (datetime.date | Unset):
        due_date_to (datetime.date | Unset):
        per_page (int | Unset):  Default: 15.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | OrderListResponse | ValidationErrorResponse
    """

    return sync_detailed(
        client=client,
        search=search,
        status_code=status_code,
        tags=tags,
        tags_any=tags_any,
        financial_status=financial_status,
        fulfillment_status=fulfillment_status,
        exclude_cancelled=exclude_cancelled,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        per_page=per_page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = UNSET,
    status_code: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    tags_any: list[str] | Unset = UNSET,
    financial_status: list[ListOrdersFinancialStatusItem] | Unset = UNSET,
    fulfillment_status: list[ListOrdersFulfillmentStatusItem] | Unset = UNSET,
    exclude_cancelled: bool | Unset = UNSET,
    due_date_from: datetime.date | Unset = UNSET,
    due_date_to: datetime.date | Unset = UNSET,
    per_page: int | Unset = 15,
) -> Response[ErrorResponse | OrderListResponse | ValidationErrorResponse]:
    """Retrieve a paginated list of orders

     Limited to 60 requests per minute.

    Args:
        search (str | Unset):
        status_code (str | Unset):
        tags (list[str] | Unset):
        tags_any (list[str] | Unset):
        financial_status (list[ListOrdersFinancialStatusItem] | Unset):
        fulfillment_status (list[ListOrdersFulfillmentStatusItem] | Unset):
        exclude_cancelled (bool | Unset):
        due_date_from (datetime.date | Unset):
        due_date_to (datetime.date | Unset):
        per_page (int | Unset):  Default: 15.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | OrderListResponse | ValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        status_code=status_code,
        tags=tags,
        tags_any=tags_any,
        financial_status=financial_status,
        fulfillment_status=fulfillment_status,
        exclude_cancelled=exclude_cancelled,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        per_page=per_page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = UNSET,
    status_code: str | Unset = UNSET,
    tags: list[str] | Unset = UNSET,
    tags_any: list[str] | Unset = UNSET,
    financial_status: list[ListOrdersFinancialStatusItem] | Unset = UNSET,
    fulfillment_status: list[ListOrdersFulfillmentStatusItem] | Unset = UNSET,
    exclude_cancelled: bool | Unset = UNSET,
    due_date_from: datetime.date | Unset = UNSET,
    due_date_to: datetime.date | Unset = UNSET,
    per_page: int | Unset = 15,
) -> ErrorResponse | OrderListResponse | ValidationErrorResponse | None:
    """Retrieve a paginated list of orders

     Limited to 60 requests per minute.

    Args:
        search (str | Unset):
        status_code (str | Unset):
        tags (list[str] | Unset):
        tags_any (list[str] | Unset):
        financial_status (list[ListOrdersFinancialStatusItem] | Unset):
        fulfillment_status (list[ListOrdersFulfillmentStatusItem] | Unset):
        exclude_cancelled (bool | Unset):
        due_date_from (datetime.date | Unset):
        due_date_to (datetime.date | Unset):
        per_page (int | Unset):  Default: 15.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | OrderListResponse | ValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            status_code=status_code,
            tags=tags,
            tags_any=tags_any,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            exclude_cancelled=exclude_cancelled,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            per_page=per_page,
        )
    ).parsed
