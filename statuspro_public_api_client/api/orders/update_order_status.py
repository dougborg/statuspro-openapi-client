from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.message_response import MessageResponse
from ...models.update_order_status_request import UpdateOrderStatusRequest
from ...models.validation_error_response import ValidationErrorResponse


def _get_kwargs(
    order: int,
    *,
    body: UpdateOrderStatusRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/orders/{order}/status".format(
            order=quote(str(order), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | MessageResponse | ValidationErrorResponse | None:
    if response.status_code == 200:
        response_200 = MessageResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[ErrorResponse | MessageResponse | ValidationErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    order: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateOrderStatusRequest,
) -> Response[ErrorResponse | MessageResponse | ValidationErrorResponse]:
    """Update an order status

     Limited to 60 requests per minute.

    Args:
        order (int):
        body (UpdateOrderStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | MessageResponse | ValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        order=order,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    order: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateOrderStatusRequest,
) -> ErrorResponse | MessageResponse | ValidationErrorResponse | None:
    """Update an order status

     Limited to 60 requests per minute.

    Args:
        order (int):
        body (UpdateOrderStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | MessageResponse | ValidationErrorResponse
    """

    return sync_detailed(
        order=order,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    order: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateOrderStatusRequest,
) -> Response[ErrorResponse | MessageResponse | ValidationErrorResponse]:
    """Update an order status

     Limited to 60 requests per minute.

    Args:
        order (int):
        body (UpdateOrderStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | MessageResponse | ValidationErrorResponse]
    """

    kwargs = _get_kwargs(
        order=order,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    order: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateOrderStatusRequest,
) -> ErrorResponse | MessageResponse | ValidationErrorResponse | None:
    """Update an order status

     Limited to 60 requests per minute.

    Args:
        order (int):
        body (UpdateOrderStatusRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | MessageResponse | ValidationErrorResponse
    """

    return (
        await asyncio_detailed(
            order=order,
            client=client,
            body=body,
        )
    ).parsed
