"""Thin CRUD wrappers for all StatusPro API resources.

Usage::

    async with StatusProClient() as client:
        products = await client.api.products.list(is_sellable=True)
        product = await client.api.products.get(123)
        await client.api.products.delete(123)
"""

from ._namespace import ApiNamespace
from ._registry import RESOURCE_REGISTRY, ResourceConfig
from ._resource import Resource

__all__ = ["RESOURCE_REGISTRY", "ApiNamespace", "Resource", "ResourceConfig"]
