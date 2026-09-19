# Replacement Catalog

Worked examples of bespoke machinery and the established solutions for the same named problem. This is a prompt for what to look for, not a menu. Confirm current capabilities, maintenance, and licensing in primary documentation before recommending anything, and prefer a facility the repository already depends on over a new one.

## Symptom to named problem

| What you see in the code | Named problem | Where to look |
|---|---|---|
| String substitution, `{% %}`-style tags, an include resolver, an escaping helper | Templating | Jinja, Twig, Liquid, the framework's own template engine |
| A scheduler, a retry table, a timer loop, resume-after-crash logic | Durable execution | Temporal, a broker's native delay and retry, a database-backed state machine |
| Validation models, wire serializers, docs, and client types kept in agreement | Interface description | OpenAPI, JSON Schema, protobuf, framework-native contract generation |
| Hand-written parse and dump functions with per-field coercion | Validation and serialization | Pydantic, Zod, the framework's serializer layer |
| Trace ID plumbing, span stitching, a vendor-specific exporter | Telemetry | OpenTelemetry API, SDK, OTLP, Collector |
| Accumulating booleans, `isLoading`/`isError`/`isDirty`, impossible combinations | State modeling | Statecharts (XState), an explicit finite-state model in the database |
| Nested permission walks over folders, teams, and shares | Authorization | OpenFGA and Zanzibar-style engines, policy engines, framework permissions |
| Password hashing, session cookies, token refresh, CSRF handling | Authentication | Framework auth subsystems, an identity provider |
| `argv` slicing, a help-text builder, a completion script | Command-line interfaces | Click, Typer, Cobra |
| Hand-written schema change scripts, a version table | Migrations | The ORM's migration generator |
| A rules table interpreted by a bespoke evaluator | Policy or expression evaluation | CEL, OPA, Cedar |
| Boolean toggles read from config and branched on everywhere | Feature flags | OpenFeature and its providers |
| A tokenizer and recursive-descent parser for a known format | Parsing | The format's standard parser, tree-sitter for source code |
| Env parsing with layered defaults and per-environment branches | Configuration | Framework config plus twelve-factor environment config |

## Worked examples

### Templating

A bespoke engine that grows variables, conditionals, includes, inheritance, escaping, a loader, and a cache has reimplemented [Jinja](https://jinja.palletsprojects.com/), which ships template inheritance, macros, imports, autoescaping, configurable loaders, compiled-template caching, async rendering, and extension points for filters, tests, and tags.

The decisive detail is usually untrusted input. Jinja provides a sandboxed environment for rendering untrusted templates; a bespoke evaluator almost never has an equivalent threat model. Sandboxing alone is not sufficient either: pass inert data, cap output size, and enforce timeouts and memory limits in the surrounding process.

Where it does not fit: a genuinely tiny substitution helper with no control flow, or a deliberate decision to restrict template expressiveness beyond what the engine allows.

### Durable execution

Scheduling, retry accounting, cancellation, durable timers, and crash recovery spread across modules is a distributed state machine with no owner. [Temporal](https://docs.temporal.io/) provides this as a product: persisted event history with replay-based recovery, [retry policies](https://docs.temporal.io/encyclopedia/retry-policies) with configurable backoff, and [persisted timers](https://docs.temporal.io/workflow-execution/timers-delays) that survive worker and service downtime.

Temporal is not the only rung. When requirements are narrower, a broker's native delayed delivery and retries, or a single database-backed state machine with atomic claims, leases, fencing tokens, and a transactional outbox, removes the same coordination sprawl at a fraction of the operational cost. Rank these against the actual durability requirement rather than defaulting to the most capable option.

Where it does not fit: short in-process work with no durability requirement, or a team that cannot absorb a new operational dependency, in which case recommend the single-owner state machine instead.

### One contract, many representations

Validation models, wire serialization, published documentation, and generated client types are four views of one contract. Maintaining them separately guarantees drift; adding a synchronization layer adds a fifth representation and more failure modes.

Make one artifact authoritative and generate the rest. [OpenAPI](https://spec.openapis.org/oas/latest) describes HTTP APIs in a language-agnostic way, and [OpenAPI Generator](https://openapi-generator.tech/) produces clients and documentation from it. Contract-first suits a stable public API and polyglot consumers; code-first generation suits a single backend whose models already match the wire shape. Keep domain validation internal and maintain exactly one explicit mapper between domain objects and generated transport types.

Where it does not fit: an internal single-language boundary where the language's own type sharing is simpler, or a transport that is not HTTP or JSON.

### Telemetry

Bespoke context propagation, span stitching, and vendor-specific exporters solve a problem [OpenTelemetry](https://opentelemetry.io/docs/) standardized: a vendor-neutral API and SDK for traces, metrics, and logs, the OTLP wire format, and a Collector that receives, processes, and exports to any supported backend. The main argument for it is that it removes vendor coupling from application code entirely.

Where it does not fit: an environment already standardized on a different instrumentation stack with no path to OTLP.

### State modeling

Interacting booleans encode states implicitly and permit combinations that should be impossible. [Statecharts](https://stately.ai/docs/state-machines-and-statecharts) make states finite and explicit, transitions deterministic and event-driven, and data separate from state, with hierarchy and parallelism for the complex cases.

Adopting a library is optional; adopting the model is the point. For persisted workflows, the equivalent move is an explicit state column with an enumerated transition table rather than a set of independent flags.

### Authorization

Recursive permission walks over folders, teams, organizations, and shares are a relationship graph. [OpenFGA](https://openfga.dev/docs/fga) implements the Zanzibar model: a typed schema of types and relations, relationship tuples, `check` for forward decisions, and `list-objects` for reverse queries such as "everything this user can read".

Choose by the shape of the problem. Relationship engines suit hierarchy and sharing. Policy engines suit attribute and environment rules. Plain framework permissions suit flat roles, and reaching past them is over-engineering.

## Migration patterns

Recommend a path that keeps the system releasable at every step:

- [Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html) — place an interface between callers and the current implementation, build the replacement behind it, switch callers, then delete the old implementation.
- [Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html) — move behavior capability by capability into the replacement until nothing reaches the original.
- [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html) — expand, migrate, contract, when the contract itself must change.

Capture characterization tests of current behavior before the swap, compare fixtures across it, and keep behavior-preserving migration separate from deliberate behavior changes.
