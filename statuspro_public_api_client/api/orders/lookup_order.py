from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response
from ...models.error_response import ErrorResponse
from ...models.order_response import OrderResponse


def _get_kwargs(
    *,
    number: str,
    email: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["number"] = number

    params["email"] = email

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/orders/lookup",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | OrderResponse | None:
    if response.status_code == 200:
        response_200 = OrderResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[ErrorResponse | OrderResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    number: str,
    email: str,
) -> Response[ErrorResponse | OrderResponse]:
    """Retrieve an order by order number and customer email

     Limited to 60 requests per minute.

    Args:
        number (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | OrderResponse]
    """

    kwargs = _get_kwargs(
        number=number,
        email=email,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    number: str,
    email: str,
) -> ErrorResponse | OrderResponse | None:
    """Retrieve an order by order number and customer email

     Limited to 60 requests per minute.

    Args:
        number (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | OrderResponse
    """

    return sync_detailed(
        client=client,
        number=number,
        email=email,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    number: str,
    email: str,
) -> Response[ErrorResponse | OrderResponse]:
    """Retrieve an order by order number and customer email

     Limited to 60 requests per minute.

    Args:
        number (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | OrderResponse]
    """

    kwargs = _get_kwargs(
        number=number,
        email=email,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    number: str,
    email: str,
) -> ErrorResponse | OrderResponse | None:
    """Retrieve an order by order number and customer email

     Limited to 60 requests per minute.

    Args:
        number (str):
        email (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | OrderResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            number=number,
            email=email,
        )
    ).parsed
