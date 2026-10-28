# Elysia 2 release notes (reference)

Kept as a reference for the NEXA edge stack (Bun and Elysia 2, see [`docs/design/tech-stack.md`](../docs/design/tech-stack.md)). This is a condensed summary of the official post, not a copy. The source stays the truth.

- Source: [Elysia 2 beta, "DayDream"](https://elysiajs.com/blog/elysia-20.html) (section the team pointed to: [Tree shake TypeBox](https://elysiajs.com/blog/elysia-20.html#tree-shake-typebox))
- Read on: 2026-10-28. The page at this address is labelled **beta**. The later release candidate has its own post, cited in `tech-stack.md`.
- Status in NEXA: reference only. Nothing in the design is fixed by this page (open item O-34 covers the version pin and the error body).

## What the post says

### Why it matters
- Elysia 2 is a complete rewrite. The goals are smaller bundle, faster startup and lower memory, not more throughput. The post says not to expect much higher throughput.
- Install the beta with `bun add elysia@next`. Automatic migration from 1.x: `bunx @elysia/codemod@latest` (the post says about 95% of the code is converted).

### Bundle size (tree shake TypeBox)
Un-minified "hello world" sizes, Elysia 1 against Elysia 2:

| Validator | Elysia 1 | Elysia 2 |
| --- | --- | --- |
| None | 736 KB | 344 KB |
| TypeBox | 736 KB | 847 KB |
| Valibot | 742 KB | 350 KB |
| Zod | 1,260 KB | 868 KB |

- TypeBox can now be removed from the bundle entirely when it is not used. Elysia 1 always bundled it.
- With the ahead-of-time (AOT) build plugin, Elysia 2 shrinks further: 226 KB with no validator, 288 KB with TypeBox. Minified, the no-validator build is 141 KB.
- TypeBox moved from 0.34 to 1.3. Cookie schemas can be set per field. `t.Accelerate` (alpha) converts a Standard Schema such as Zod to the TypeBox compiler.

### Startup and memory
- Startup is more than 30% faster. At 25 routes with schemas: Elysia 24 ms, Elysia with TypeBox 28 ms, Elysia with Zod 38 ms.
- After a load test the post reports 45.7 MB for Elysia 2, against 73.9 MB for Hono and 192.4 MB for Fastify. In cluster mode memory is roughly multiplied by the worker count.
- AOT compilation moves the route and schema compile step to build time (`Bun.build`, Vite, esbuild, Rspack or unplugin). The build does a dry run of the app, so long-running connections (database pools) need `process.exit(0)` after the build, and `Manifest.isCapturing()` can skip parts of the app during that dry run. The post recommends AOT for Cloudflare Workers.

### Runtime and adapters
- Elysia keeps using Web Standard Request and Response. Adapter v2 is public (`createAdapter`). Node runs through `@elysia/node` (built on `srvx` and `crossws`). Node WebSocket is a separate import.
- New `defer(() => ...)` runs a callback after the response is sent, after the `afterResponse` hook.

### Breaking changes to watch (beta post)
- Route signature: hook or schema comes before the handler: `.post('/', { body: ... }, handler)`.
- The `@elysia` npm scope now holds official plugins for Elysia 1.4 and later. `@elysiajs` keeps the Elysia 1.x plugins.
- Lifecycle events lose the `on` prefix in the beta (`onBeforeHandle` becomes `beforeHandle`, `onStart` becomes `setup`, `onStop` becomes `cleanup`). NEXA note: `tech-stack.md` records that the release candidate went back to the `on` names, so check the version before copying code.
- Errors: `.error(MyError, handler)` takes the error class, and the string error codes are gone. Error types flow into route response types, so Eden and OpenAPI can list the errors.
- Errors use RFC 9457 problem details with `application/problem+json`. The `problem(status, { detail })` helper opts in. Clients other than Eden must be checked. NEXA keeps its own error body for now (O-34).
- Unhandled errors no longer leak their message when `NODE_ENV=production`. Errors with status 500 or above without an explicit response return `Internal Server Error`.
- `.macro(name, definition)` is removed in favour of `.macro({ ... })`. `resolve` is now `derive` (runs in `beforeHandle`). The `scoped` scope is renamed `plugin`, and the `{ as: ... }` object form is removed. `guard` and `group` now override inherited schemas by default, so additive behaviour needs `schema: 'standalone'`.
- WebSocket is opt-in: `.use(websocket())` from `elysia/websocket`, `.ws()` takes `(path, options, handler)`, and generator `yield` is the preferred way to send.
- `aot: false` (dynamic mode) is removed. The `file-type` package is no longer bundled, so call `setFileTypeDetector` for `t.File` type checks.
- Smaller behaviour changes include read-only `context.path`, lazy signed-cookie verification, 415 when the content type is unclear, and the 422 validation response no longer echoing request bodies over 4 KB.

### Status the post gives
- Elysia 2 is a beta. The team says it is stable enough for their own apps and will keep the beta label until a good share of plugins have moved to Elysia 2.

## Questions this raises for NEXA
- Which exact version do we pin, and when do we move to the final release? (O-34)
- Do all the Elysia plugins we plan to use support Elysia 2? (checked per plugin in `tech-stack.md`)
- Do we adopt the AOT build plugin for the edge apps, given the dry-run rule for database pools and the Cloudflare notes? This is not decided yet.
