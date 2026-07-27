# Changelog

## [1.0.0](https://github.com/dougborg/statuspro-openapi-client/compare/mcp-v0.2.0...mcp-v1.0.0) (2026-07-27)


### ⚠ BREAKING CHANGES

* **mcp:** the `lookup_order` MCP tool no longer exists. Use `list_orders(search=…)` or `get_order(id=…)`.

### Features

* get_order history truncation + get_order_history tool ([#43](https://github.com/dougborg/statuspro-openapi-client/issues/43)) ([650f5c7](https://github.com/dougborg/statuspro-openapi-client/commit/650f5c75610163d61500c575184971b15d4e4e14))
* initial statuspro-openapi-client monorepo ([4507485](https://github.com/dougborg/statuspro-openapi-client/commit/45074854aafb4b6d0fad900186f63949074ec1e8))
* **mcp:** add batch read tools — get_orders_batch, lookup_orders_batch, summarize_active_orders ([#49](https://github.com/dougborg/statuspro-openapi-client/issues/49)) ([87af369](https://github.com/dougborg/statuspro-openapi-client/commit/87af36951e372306f6d1b98c396846a809a5fa4f))
* **mcp:** add list_orders_in_workflow + document list_orders gotchas ([#50](https://github.com/dougborg/statuspro-openapi-client/issues/50)) ([0368ce9](https://github.com/dougborg/statuspro-openapi-client/commit/0368ce9e42ef2e392f63ee622cc5eeede78ff12f))
* **mcp:** drop lookup_order tool from MCP surface ([#42](https://github.com/dougborg/statuspro-openapi-client/issues/42)) ([dbd06fe](https://github.com/dougborg/statuspro-openapi-client/commit/dbd06fea0c4ca94948ce5790c3465dcaa53dc6c3))
* **mcp:** package server as MCPB (.mcpb) for one-click Claude Desktop install ([#62](https://github.com/dougborg/statuspro-openapi-client/issues/62)) ([78edbe8](https://github.com/dougborg/statuspro-openapi-client/commit/78edbe89208b80c2f8ec40426407068e9f138077))
* **mcp:** Prefab UI parity for the 3 remaining mutations ([#46](https://github.com/dougborg/statuspro-openapi-client/issues/46)) ([d09d418](https://github.com/dougborg/statuspro-openapi-client/commit/d09d418c0c1ee020d700c78e9258de2635610c37))
* **mcp:** preview-card confirm rail + fix ForEach history templating ([#83](https://github.com/dougborg/statuspro-openapi-client/issues/83)) ([f53a14b](https://github.com/dougborg/statuspro-openapi-client/commit/f53a14b4ecd0c9d28d0c6282d608c4c94a50ac0f))
* **mcp:** render Prefab UI for the find/view/decide/mutate cluster ([#20](https://github.com/dougborg/statuspro-openapi-client/issues/20)) ([f01ce5f](https://github.com/dougborg/statuspro-openapi-client/commit/f01ce5f0ff87dc5f628be9cc046a1f144fe4dcec))
* **mcp:** update_order_status preview self-validates against viable transitions ([#44](https://github.com/dougborg/statuspro-openapi-client/issues/44)) ([e9c3f37](https://github.com/dougborg/statuspro-openapi-client/commit/e9c3f37ba40adf5259a4d17ad746285810145bab))
* **release:** migrate to release-please manifest-mode release automation ([#128](https://github.com/dougborg/statuspro-openapi-client/issues/128)) ([11ad7bf](https://github.com/dougborg/statuspro-openapi-client/commit/11ad7bf5996fea9a329884491f9788495ce4b4e2))


### Bug Fixes

* **docs:** repoint docs symlinks to StatusPro packages; rewrite stale ADR examples ([d111f35](https://github.com/dougborg/statuspro-openapi-client/commit/d111f357109ae6f17b6c461ff2cec1ddb48e31bf))
* **mcp:** address Copilot review feedback from [#42](https://github.com/dougborg/statuspro-openapi-client/issues/42), [#43](https://github.com/dougborg/statuspro-openapi-client/issues/43), [#44](https://github.com/dougborg/statuspro-openapi-client/issues/44) ([#45](https://github.com/dougborg/statuspro-openapi-client/issues/45)) ([0b67bdd](https://github.com/dougborg/statuspro-openapi-client/commit/0b67bddcff63ce870ebb09986247d081017692d0))
* **mcp:** canonical confirmation flow — drop elicitation gate, use CallTool for prefab buttons ([#52](https://github.com/dougborg/statuspro-openapi-client/issues/52)) ([8786cb0](https://github.com/dougborg/statuspro-openapi-client/commit/8786cb0716747656717996fe8a60870e4a214678))
* **release:** drop PSR build_command that cannot run in its container ([#125](https://github.com/dougborg/statuspro-openapi-client/issues/125)) ([584f1fe](https://github.com/dougborg/statuspro-openapi-client/commit/584f1fee187fb9c05e366fbb716ea320de2dd911)), closes [#124](https://github.com/dougborg/statuspro-openapi-client/issues/124)
* stabilize CI — bump timing test tolerance, fix TS release OIDC flow ([#6](https://github.com/dougborg/statuspro-openapi-client/issues/6)) ([ad1dded](https://github.com/dougborg/statuspro-openapi-client/commit/ad1ddedd9da5f35e3e43734c3b9cd63dff2a8c84))
* **tests:** align MCP package asyncio_mode with the root ([#127](https://github.com/dougborg/statuspro-openapi-client/issues/127)) ([f250f19](https://github.com/dougborg/statuspro-openapi-client/commit/f250f19f42a237fbe67dc76e436292d484c89940))

## [0.2.0](https://github.com/dougborg/statuspro-openapi-client/compare/mcp-v0.1.0...mcp-v0.2.0) (2026-07-27)


### Features

* **release:** migrate to release-please manifest-mode release automation ([#128](https://github.com/dougborg/statuspro-openapi-client/issues/128)) ([11ad7bf](https://github.com/dougborg/statuspro-openapi-client/commit/11ad7bf5996fea9a329884491f9788495ce4b4e2))


### Bug Fixes

* **tests:** align MCP package asyncio_mode with the root ([#127](https://github.com/dougborg/statuspro-openapi-client/issues/127)) ([f250f19](https://github.com/dougborg/statuspro-openapi-client/commit/f250f19f42a237fbe67dc76e436292d484c89940))

## CHANGELOG

All notable changes to the StatusPro MCP Server will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
