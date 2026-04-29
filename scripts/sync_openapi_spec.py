#!/usr/bin/env python3
"""Pull the upstream StatusPro OpenAPI spec, normalize to YAML for diffing.

The local spec at ``docs/statuspro-openapi.yaml`` is a fork: we evolve it
locally to add params/endpoints the upstream spec doesn't yet declare (e.g.
the ``page`` query parameter for ``GET /orders`` added in #27). This script
fetches the canonical upstream spec, converts it to YAML with deterministic
ordering and width, and writes it to ``docs/statuspro-openapi.upstream.yaml``
so a regular ``git diff`` against the local fork surfaces upstream deltas
cleanly.

The intended workflow:

1. ``uv run poe sync-openapi-spec`` — pulls latest upstream into
   ``docs/statuspro-openapi.upstream.yaml``.
2. ``git diff docs/statuspro-openapi.upstream.yaml`` — see what changed
   upstream since last sync.
3. Reconcile interesting deltas into the local fork
   (``docs/statuspro-openapi.yaml``) by hand.
4. Run ``uv run poe regenerate-client`` to refresh the generated client.

This script does NOT auto-merge upstream into the fork — the merge is a
human judgment call (e.g. "did upstream rename a param we already added?").

Configure the upstream URL with ``STATUSPRO_OPENAPI_URL`` if the public
endpoint changes.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

DEFAULT_UPSTREAM_URL = "https://orderstatuspro.com/api/openapi.json"
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "statuspro-openapi.upstream.yaml"
)


def fetch_upstream_spec(url: str, *, timeout: int = 30) -> dict[str, Any]:
    """Download the upstream OpenAPI spec as a parsed dict."""
    print(f"Fetching upstream spec: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "statuspro-openapi-client/sync",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("content-type", "")
            body = resp.read()
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code} fetching {url}: {e.reason}", file=sys.stderr)
        raise SystemExit(2) from e
    except urllib.error.URLError as e:
        print(f"ERROR: failed to fetch {url}: {e.reason}", file=sys.stderr)
        raise SystemExit(2) from e

    if "json" in content_type.lower():
        return json.loads(body)
    if "yaml" in content_type.lower() or "yml" in content_type.lower():
        return yaml.safe_load(body)
    # Fall back: try JSON first (the documented endpoint serves JSON), then YAML.
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return yaml.safe_load(body)


# OpenAPI conventional top-level key order. Following this at the document
# root keeps the synced YAML readable to humans familiar with OpenAPI specs
# AND keeps diffs against the local fork (which uses the same convention)
# free of pure-reordering churn.
_OPENAPI_TOP_LEVEL_ORDER = (
    "openapi",
    "info",
    "jsonSchemaDialect",
    "servers",
    "security",
    "tags",
    "paths",
    "webhooks",
    "components",
    "externalDocs",
)


def _ordered(d: dict[str, Any], preferred: tuple[str, ...]) -> dict[str, Any]:
    """Return a new dict with keys in ``preferred`` order first, then the rest sorted."""
    result: dict[str, Any] = {}
    for key in preferred:
        if key in d:
            result[key] = d[key]
    for key in sorted(d.keys()):
        if key not in result:
            result[key] = d[key]
    return result


def normalize(value: Any, *, _is_root: bool = False) -> Any:
    """Recursively sort dict keys for deterministic YAML output.

    At the document root, top-level keys follow OpenAPI convention
    (``openapi``, ``info``, ``servers``, ``security``, ``tags``, ``paths``,
    ``components``, ...) so the synced file reads like a normal OpenAPI doc
    and diffs against the local fork show real content changes, not
    reordering noise. Below the root, keys are sorted alphabetically — that
    gives stable diffs across upstream regenerations even if the server
    reshuffles dict ordering.

    Lists keep their original order (path order, parameter order, etc. in
    OpenAPI is positionally meaningful for at least some consumers).
    """
    if isinstance(value, dict):
        if _is_root:
            ordered = _ordered(value, _OPENAPI_TOP_LEVEL_ORDER)
            return {k: normalize(ordered[k]) for k in ordered}
        return {k: normalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def dump_yaml(data: dict[str, Any]) -> str:
    """Render a dict as YAML with settings that keep diffs minimal."""
    return yaml.safe_dump(
        data,
        default_flow_style=False,  # block style — line-by-line diffs
        sort_keys=False,  # we sort upstream of this; preserve our order
        width=100,  # consistent line wrapping
        allow_unicode=True,
        indent=2,
    )


def main() -> int:
    upstream_url = os.environ.get("STATUSPRO_OPENAPI_URL", DEFAULT_UPSTREAM_URL)
    output_path_str = os.environ.get("STATUSPRO_OPENAPI_OUTPUT")
    output_path = Path(output_path_str) if output_path_str else DEFAULT_OUTPUT_PATH

    spec = fetch_upstream_spec(upstream_url)
    if not isinstance(spec, dict):
        print(
            f"ERROR: upstream returned non-dict shape: {type(spec).__name__}",
            file=sys.stderr,
        )
        return 2

    info = spec.get("info") or {}
    print(
        f"Upstream: {info.get('title', '?')} v{info.get('version', '?')} "
        f"(openapi {spec.get('openapi', '?')})"
    )
    print(f"  paths: {len(spec.get('paths') or {})}")
    print(f"  schemas: {len((spec.get('components') or {}).get('schemas') or {})}")

    normalized = normalize(spec, _is_root=True)
    yaml_text = dump_yaml(normalized)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Write a small banner so readers know this is auto-generated.
    banner = (
        "# AUTO-GENERATED — DO NOT EDIT. Regenerate with: uv run poe sync-openapi-spec\n"
        f"# Upstream: {upstream_url}\n"
        f"# This is the unmerged upstream view; the local fork lives at\n"
        f"# docs/statuspro-openapi.yaml. Diff this file against the fork to see\n"
        f"# what changed upstream since last sync.\n"
    )
    output_path.write_text(banner + yaml_text)
    print(f"\nWrote {output_path} ({output_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
