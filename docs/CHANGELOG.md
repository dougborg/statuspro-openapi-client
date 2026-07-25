# CHANGELOG

<!-- version list -->

## v0.2.0 (2026-07-25)

### Bug Fixes

- **ci**: Use GitHub App token for upstream OpenAPI sync PR
  ([#120](https://github.com/dougborg/statuspro-openapi-client/pull/120),
  [`db41e1e`](https://github.com/dougborg/statuspro-openapi-client/commit/db41e1e65a1b5c4adffe2ab1916f1c136bfe0bd7))

- **client**: Repair list_orders pagination and add missing page param
  ([#27](https://github.com/dougborg/statuspro-openapi-client/pull/27),
  [`f4c46b0`](https://github.com/dougborg/statuspro-openapi-client/commit/f4c46b045b0ad86610e4e0615455dda9136afcde))

- **mcp**: Address Copilot review feedback from #42, #43, #44
  ([#45](https://github.com/dougborg/statuspro-openapi-client/pull/45),
  [`0b67bdd`](https://github.com/dougborg/statuspro-openapi-client/commit/0b67bddcff63ce870ebb09986247d081017692d0))

- **mcp**: Canonical confirmation flow — drop elicitation gate, use CallTool for prefab buttons
  ([#52](https://github.com/dougborg/statuspro-openapi-client/pull/52),
  [`8786cb0`](https://github.com/dougborg/statuspro-openapi-client/commit/8786cb0716747656717996fe8a60870e4a214678))

- **mcp**: Coerce LLM-mistyped list inputs back into Python lists
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))

- **mcp**: Correct latent type errors pyright surfaced
  ([#67](https://github.com/dougborg/statuspro-openapi-client/pull/67),
  [`f280520`](https://github.com/dougborg/statuspro-openapi-client/commit/f2805207abd139336dca8f9ac6bef24ee0b135d4))

- **release**: Drop PSR build_command that cannot run in its container
  ([#125](https://github.com/dougborg/statuspro-openapi-client/pull/125),
  [`584f1fe`](https://github.com/dougborg/statuspro-openapi-client/commit/584f1fee187fb9c05e366fbb716ea320de2dd911))

- **release**: Sync-lockfile must start from the post-release main tip
  ([#121](https://github.com/dougborg/statuspro-openapi-client/pull/121),
  [`7efd5ab`](https://github.com/dougborg/statuspro-openapi-client/commit/7efd5ab5add47a94f12df3eed573522ab1bda00f))

- **spec**: Exclude auto-generated upstream snapshot from yamllint
  ([#47](https://github.com/dougborg/statuspro-openapi-client/pull/47),
  [`e14b3f1`](https://github.com/dougborg/statuspro-openapi-client/commit/e14b3f1840e538a44a4066f521c052960ffdd7f5))

- **spec**: Validate URL scheme before fetching to satisfy SAST
  ([#47](https://github.com/dougborg/statuspro-openapi-client/pull/47),
  [`e14b3f1`](https://github.com/dougborg/statuspro-openapi-client/commit/e14b3f1840e538a44a4066f521c052960ffdd7f5))

- **ts**: Align tsconfig with TypeScript 6
  ([#17](https://github.com/dougborg/statuspro-openapi-client/pull/17),
  [`f5d5fe6`](https://github.com/dougborg/statuspro-openapi-client/commit/f5d5fe6462742bd54bd1abb0a0f1a09d10af6326))

- **ts**: Migrate biome config to v2 schema
  ([#16](https://github.com/dougborg/statuspro-openapi-client/pull/16),
  [`08a3512`](https://github.com/dougborg/statuspro-openapi-client/commit/08a35121dd75a251bbb90cd24496875a2f188788))

- **ts**: Upgrade packageManager to pnpm@10.33.0
  ([#15](https://github.com/dougborg/statuspro-openapi-client/pull/15),
  [`5ccf94e`](https://github.com/dougborg/statuspro-openapi-client/commit/5ccf94eedac8e3992c84c80ee8495e8c8dbe215b))

### Chores

- Add pre-push hook blocking direct pushes to main from non-main branches
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))

- Align with katana-openapi-client safety + MCP fixes
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))

- Bootstrap claude harness from harness-kit plugin
  ([#24](https://github.com/dougborg/statuspro-openapi-client/pull/24),
  [`9aa5db8`](https://github.com/dougborg/statuspro-openapi-client/commit/9aa5db85dcd0abe380c3c0cb31e4793f76635b7c))

- Complete mdformat → prettier swap (mcp build, docs)
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- Replace mdformat with prettier for markdown formatting
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- Replace mdformat with prettier; bump TS and Python deps
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- **actions)(deps**: Bump aquasecurity/trivy-action
  ([#21](https://github.com/dougborg/statuspro-openapi-client/pull/21),
  [`54a4f50`](https://github.com/dougborg/statuspro-openapi-client/commit/54a4f505628e89fc9f47b384f89a96020570f9d3))

- **actions)(deps**: Bump GitHub Actions to latest
  ([#84](https://github.com/dougborg/statuspro-openapi-client/pull/84),
  [`6ddb271`](https://github.com/dougborg/statuspro-openapi-client/commit/6ddb2710541d72c3496c305f5d64e47cfef39927))

- **actions)(deps**: Bump peter-evans/create-pull-request
  ([#64](https://github.com/dougborg/statuspro-openapi-client/pull/64),
  [`6ad4c46`](https://github.com/dougborg/statuspro-openapi-client/commit/6ad4c461b99ed9e962fe9b07421373950172b2cf))

- **ci**: Add weekly upstream OpenAPI spec sync workflow
  ([#48](https://github.com/dougborg/statuspro-openapi-client/pull/48),
  [`f23fe4a`](https://github.com/dougborg/statuspro-openapi-client/commit/f23fe4a1bf93e0f2f1f892462d5bb4e0d6ae5e67))

- **deps**: Bump Python deps to latest minor/patch
  ([#84](https://github.com/dougborg/statuspro-openapi-client/pull/84),
  [`6ddb271`](https://github.com/dougborg/statuspro-openapi-client/commit/6ddb2710541d72c3496c305f5d64e47cfef39927))

- **deps**: Consolidated bump of Python, npm, and Actions dependencies
  ([#84](https://github.com/dougborg/statuspro-openapi-client/pull/84),
  [`6ddb271`](https://github.com/dougborg/statuspro-openapi-client/commit/6ddb2710541d72c3496c305f5d64e47cfef39927))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 4 updates
  ([#66](https://github.com/dougborg/statuspro-openapi-client/pull/66),
  [`9f7cf75`](https://github.com/dougborg/statuspro-openapi-client/commit/9f7cf7560138e48ccc80daa85c232d0f4d07fafd))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 4 updates
  ([#26](https://github.com/dougborg/statuspro-openapi-client/pull/26),
  [`e2640a1`](https://github.com/dougborg/statuspro-openapi-client/commit/e2640a159e0a5c5a0c27069bfe3db9232578ce05))

- **deps)(py**: Update python deps and bump prefab-ui to 0.19
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- **deps)(ts**: Bump semantic-release ecosystem to v25 and @types/node to v25
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- **mcp**: Tighten coerce_str_list_input per /simplify pass
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))

- **mcp**: Use ShowToast for Cancel buttons (drop SendMessage round-trip)
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))

- **ts)(deps-dev**: Bump @biomejs/biome from 1.9.4 to 2.4.12
  ([#10](https://github.com/dougborg/statuspro-openapi-client/pull/10),
  [`1f97799`](https://github.com/dougborg/statuspro-openapi-client/commit/1f97799c5c3ee29f44ed244cf66c495d8f364b60))

- **ts)(deps-dev**: Bump npm packages to latest minor/patch
  ([#84](https://github.com/dougborg/statuspro-openapi-client/pull/84),
  [`6ddb271`](https://github.com/dougborg/statuspro-openapi-client/commit/6ddb2710541d72c3496c305f5d64e47cfef39927))

- **ts)(deps-dev**: Bump the npm-minor-patch group across 1 directory with 2 updates
  ([#25](https://github.com/dougborg/statuspro-openapi-client/pull/25),
  [`b96f47f`](https://github.com/dougborg/statuspro-openapi-client/commit/b96f47f09e851032a46b052bf1b3e270259a13b6))

- **ts)(deps-dev**: Bump the npm-minor-patch group with 2 updates
  ([#65](https://github.com/dougborg/statuspro-openapi-client/pull/65),
  [`983beef`](https://github.com/dougborg/statuspro-openapi-client/commit/983beef421f716ed993892b8c86ea79c3bf642db))

- **ts)(deps-dev**: Bump typescript from 5.9.3 to 6.0.3
  ([#13](https://github.com/dougborg/statuspro-openapi-client/pull/13),
  [`87c0dcf`](https://github.com/dougborg/statuspro-openapi-client/commit/87c0dcf0b8be4bac3b0efc17c3311cd6dac61cf8))

### Code Style

- **docs**: Satisfy prettier in workflows README
  ([#121](https://github.com/dougborg/statuspro-openapi-client/pull/121),
  [`7efd5ab`](https://github.com/dougborg/statuspro-openapi-client/commit/7efd5ab5add47a94f12df3eed573522ab1bda00f))

### Continuous Integration

- Add pnpm to release workflow; tighten changelog exclude
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- Install pnpm where format-check runs
  ([#18](https://github.com/dougborg/statuspro-openapi-client/pull/18),
  [`4c0058b`](https://github.com/dougborg/statuspro-openapi-client/commit/4c0058b147cf58df82dec656009fd37ae10b4056))

- Migrate release automation from PAT to GitHub App token
  ([#121](https://github.com/dougborg/statuspro-openapi-client/pull/121),
  [`7efd5ab`](https://github.com/dougborg/statuspro-openapi-client/commit/7efd5ab5add47a94f12df3eed573522ab1bda00f))

- **mcp**: Build .mcpb on MCP releases and attach to GitHub release
  ([#62](https://github.com/dougborg/statuspro-openapi-client/pull/62),
  [`78edbe8`](https://github.com/dougborg/statuspro-openapi-client/commit/78edbe89208b80c2f8ec40426407068e9f138077))

### Documentation

- Capture retro learnings — Copilot review wait + structural test asserts
  ([#58](https://github.com/dougborg/statuspro-openapi-client/pull/58),
  [`c5025e6`](https://github.com/dougborg/statuspro-openapi-client/commit/c5025e6a8770ab44f6b320fb603b50f0fcc66e40))

- **harness**: Adopt /open-pr push-refspec safety + worktree note
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))

- **mcp**: Document .mcpb install path as the recommended Claude Desktop flow
  ([#62](https://github.com/dougborg/statuspro-openapi-client/pull/62),
  [`78edbe8`](https://github.com/dougborg/statuspro-openapi-client/commit/78edbe89208b80c2f8ec40426407068e9f138077))

### Features

- Get_order history truncation + get_order_history tool
  ([#43](https://github.com/dougborg/statuspro-openapi-client/pull/43),
  [`650f5c7`](https://github.com/dougborg/statuspro-openapi-client/commit/650f5c75610163d61500c575184971b15d4e4e14))

- **mcp**: Add batch read tools — get_orders_batch, lookup_orders_batch, summarize_active_orders
  ([#49](https://github.com/dougborg/statuspro-openapi-client/pull/49),
  [`87af369`](https://github.com/dougborg/statuspro-openapi-client/commit/87af36951e372306f6d1b98c396846a809a5fa4f))

- **mcp**: Add list_orders_in_workflow + document list_orders gotchas
  ([#50](https://github.com/dougborg/statuspro-openapi-client/pull/50),
  [`0368ce9`](https://github.com/dougborg/statuspro-openapi-client/commit/0368ce9e42ef2e392f63ee622cc5eeede78ff12f))

- **mcp**: Add MCP Bundle (.mcpb) build script + manifest template
  ([#62](https://github.com/dougborg/statuspro-openapi-client/pull/62),
  [`78edbe8`](https://github.com/dougborg/statuspro-openapi-client/commit/78edbe89208b80c2f8ec40426407068e9f138077))

- **mcp**: Add Prefab UI foundation (utils, templates, schemas)
  ([#20](https://github.com/dougborg/statuspro-openapi-client/pull/20),
  [`f01ce5f`](https://github.com/dougborg/statuspro-openapi-client/commit/f01ce5f0ff87dc5f628be9cc046a1f144fe4dcec))

- **mcp**: Drop lookup_order tool from MCP surface
  ([#42](https://github.com/dougborg/statuspro-openapi-client/pull/42),
  [`dbd06fe`](https://github.com/dougborg/statuspro-openapi-client/commit/dbd06fea0c4ca94948ce5790c3465dcaa53dc6c3))

- **mcp**: Package server as MCPB (.mcpb) for one-click Claude Desktop install
  ([#62](https://github.com/dougborg/statuspro-openapi-client/pull/62),
  [`78edbe8`](https://github.com/dougborg/statuspro-openapi-client/commit/78edbe89208b80c2f8ec40426407068e9f138077))

- **mcp**: Prefab UI parity for the 3 remaining mutations
  ([#46](https://github.com/dougborg/statuspro-openapi-client/pull/46),
  [`d09d418`](https://github.com/dougborg/statuspro-openapi-client/commit/d09d418c0c1ee020d700c78e9258de2635610c37))

- **mcp**: Preview-card confirm rail + fix ForEach history templating
  ([#83](https://github.com/dougborg/statuspro-openapi-client/pull/83),
  [`f53a14b`](https://github.com/dougborg/statuspro-openapi-client/commit/f53a14b4ecd0c9d28d0c6282d608c4c94a50ac0f))

- **mcp**: Render Prefab UI for find/view/decide/mutate cluster
  ([#20](https://github.com/dougborg/statuspro-openapi-client/pull/20),
  [`f01ce5f`](https://github.com/dougborg/statuspro-openapi-client/commit/f01ce5f0ff87dc5f628be9cc046a1f144fe4dcec))

- **mcp**: Render Prefab UI for the find/view/decide/mutate cluster
  ([#20](https://github.com/dougborg/statuspro-openapi-client/pull/20),
  [`f01ce5f`](https://github.com/dougborg/statuspro-openapi-client/commit/f01ce5f0ff87dc5f628be9cc046a1f144fe4dcec))

- **mcp**: Update_order_status preview self-validates against viable transitions
  ([#44](https://github.com/dougborg/statuspro-openapi-client/pull/44),
  [`e9c3f37`](https://github.com/dougborg/statuspro-openapi-client/commit/e9c3f37ba40adf5259a4d17ad746285810145bab))

- **spec**: Add OpenAPI spec sync script and upstream snapshot
  ([#47](https://github.com/dougborg/statuspro-openapi-client/pull/47),
  [`e14b3f1`](https://github.com/dougborg/statuspro-openapi-client/commit/e14b3f1840e538a44a4066f521c052960ffdd7f5))

- **spec**: OpenAPI spec sync script + upstream snapshot
  ([#47](https://github.com/dougborg/statuspro-openapi-client/pull/47),
  [`e14b3f1`](https://github.com/dougborg/statuspro-openapi-client/commit/e14b3f1840e538a44a4066f521c052960ffdd7f5))

### Refactoring

- **mcp**: Align Prefab UI emission with MCP Apps spec (SEP-1865)
  ([#51](https://github.com/dougborg/statuspro-openapi-client/pull/51),
  [`e740df3`](https://github.com/dougborg/statuspro-openapi-client/commit/e740df3949ba3127d15b767a8f83711383d37eae))

- **mcp**: Extract OrderIdParam and ConfirmFlag tool param aliases
  ([#67](https://github.com/dougborg/statuspro-openapi-client/pull/67),
  [`f280520`](https://github.com/dougborg/statuspro-openapi-client/commit/f2805207abd139336dca8f9ac6bef24ee0b135d4))

- **mcp**: Simplify pass on the Prefab UI wiring
  ([#20](https://github.com/dougborg/statuspro-openapi-client/pull/20),
  [`f01ce5f`](https://github.com/dougborg/statuspro-openapi-client/commit/f01ce5f0ff87dc5f628be9cc046a1f144fe4dcec))

- **mcp**: Status-change confirm branch gets its own template
  ([#20](https://github.com/dougborg/statuspro-openapi-client/pull/20),
  [`f01ce5f`](https://github.com/dougborg/statuspro-openapi-client/commit/f01ce5f0ff87dc5f628be9cc046a1f144fe4dcec))

- **mcp**: Tighten tool param types + fix latent type errors pyright caught
  ([#67](https://github.com/dougborg/statuspro-openapi-client/pull/67),
  [`f280520`](https://github.com/dougborg/statuspro-openapi-client/commit/f2805207abd139336dca8f9ac6bef24ee0b135d4))

- **mcp**: Typed Rx refs for prefab Confirm args + pin no-SendMessage on Cancel
  ([#85](https://github.com/dougborg/statuspro-openapi-client/pull/85),
  [`8587b47`](https://github.com/dougborg/statuspro-openapi-client/commit/8587b4756674d7742e233b720ccbd68f1911d2b9))

- **spec**: Switch sync script from urllib to httpx + Copilot fixes
  ([#47](https://github.com/dougborg/statuspro-openapi-client/pull/47),
  [`e14b3f1`](https://github.com/dougborg/statuspro-openapi-client/commit/e14b3f1840e538a44a4066f521c052960ffdd7f5))

### Testing

- **mcp**: Mock time.perf_counter in observability timing tests
  ([#60](https://github.com/dougborg/statuspro-openapi-client/pull/60),
  [`a0a5a63`](https://github.com/dougborg/statuspro-openapi-client/commit/a0a5a63eedf9c101d9751a9cf426ecc9709e1468))


## v0.1.0 (2026-04-20)

- Initial Release

## v0.1.0 (unreleased)

Initial monorepo for the StatusPro API client ecosystem:

- `statuspro-openapi-client` — Python client with transport-layer resilience.
- `statuspro-mcp-server` — MCP server exposing the API as 9 tools.
- `statuspro-client` — TypeScript client.

Bootstrapped from the `katana-openapi-client` monorepo harness.
