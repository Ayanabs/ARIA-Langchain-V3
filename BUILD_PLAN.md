# ARIA build plan

You are building ARIA, an organizational data assistant, from scratch. `AGENTS.md` holds the
binding rules: read it before every phase, and copy it into a new repository if you start one.

This plan fixes **what** ARIA must do and the flow a request follows. It does not require the
previous implementation's structure, libraries or techniques. Use current best practice, and
choose techniques that suit the models actually deployed (see "The models"). Where this plan
recommends a technique, a better-justified alternative is welcome: say why in the phase summary.

Work in the phases at the end. Finish each phase with its checks passing, then stop and summarise
what you built, what you verified and what remains. Start each phase in a fresh session with:
"Continue with phase N of BUILD_PLAN.md."

## What ARIA is

A chat assistant for an organization. A signed-in user asks a question in natural language about
the organization's records or documents. ARIA answers from the knowledge documents (RAG), from the
backend through the registered tools, or both, and streams back a grounded answer with sources,
tables, graphs and charts.

## Test environment

Use these servers for development and testing now. Code reads every address from `.env`; this
table is for reference only. Credentials live in `.env` only; never copy them anywhere else.

| Service | `.env` key | Address |
|---|---|---|
| ARIA service (this project) | `HOST`, `PORT` | `0.0.0.0:8002` |
| Spring Boot backend | `SPRING_BOOT_BASE_URL` | `http://192.168.84.190:8080` |
| Model host (tool and synthesis models) | `OPENAI_API_BASE`, `GENERAL_OPENAI_API_BASE` | `https://colab.require.help/v1` (Ollama; its native API is also reachable at `https://colab.require.help/api/...`) |
| Embeddings (`bge-m3`) | `EMBEDDING_API_BASE` | `http://192.168.84.190:11434` |
| RAG search service | `RAG_SERVICE_URL` | `http://192.168.84.190:8082/api/search` |
| NER service | `NER_SERVICE_URL` | `http://192.168.84.190:8009/extract` |
| Cross-encoder | `CROSS_ENCODER_HOST`, `CROSS_ENCODER_PORT` | `192.168.84.190:8006` |
| Redis | `REDIS_HOST`, `REDIS_PORT` | `192.168.84.190:6379` |
| Chats database (PostgreSQL) | `CHATS_DB_HOST`, `CHATS_DB_PORT` | `192.168.84.190:5430`, database `aria_chats_db` |
| Prompts database (PostgreSQL) | `PROMPTS_DB_HOST`, `PROMPTS_DB_PORT` | `192.168.84.190:5433`, database `aria_prompts_db` |
| Frontend dev server | `VITE_GATEWAY_URL` in ARIA_Frontend | points at the ARIA service, default `http://127.0.0.1:8002` |

Spring Boot's OpenAPI and entity metadata (`/api/metadata/schema`) are served by the backend above.
Default (offline) tests must not contact any of these servers; `live` tests may.

## How the three projects connect

```
ARIA_Frontend ──/api/gateway/*──► ARIA service (port 8002) ──tools──► ARIA_Springboot (192.168.84.190:8080)
  (Vite proxies /api/gateway here and strips the prefix)  ├──► RAG service, embeddings
                                                          └──► model host
```

- **Frontend** (`D:\Work\ACCIMT\Frontend\ARIA_Frontend`, React + Vite + Chart.js) must keep working
  unchanged. Its contract is in:
  - `src/lib/chat-stream-manager.ts` (stream events);
  - `src/components/chat/types.ts` (message, tool call, record and chart shapes);
  - `vite.config.ts` (routes).

  Routes it uses:
  - queries: `/api/query/stream`, `/api/site/stream`, `/api/widget/query/stream`;
  - chats: `/api/chats` and `/api/chats/{id}` (plus `/metrics`), `/api/chat/status`;
  - RAG documents: `/api/rag/upload`, `/api/rag/ingest`, `/api/rag/documents/...`;
  - health: `/health`, `/springboot/health`, `/models/health`, `/redis/health`;
  - admin: `/api/admin/...`.

  Stream events it handles: `chat_created`, `user_prompt`, `step`, `gazetteer_status`,
  `tool_start`, `tool_result`, `tool_end`, `synthesis_start`, `thought`, `thought_token`,
  `token`, `chart`, `usage`, `ping`, `done`, `error`.
- **Spring Boot** (`D:\Work\ACCIMT\Springboot\ARIA_Springboot`) is the only source of business
  data, called as the signed-in user through registered tools. Use only capabilities it already
  exposes.

## Universal design

Nothing in ARIA's code names a specific organization, person, entity, field, tool, endpoint,
model or keyword (see `AGENTS.md`). Adding a capability must just work:

1. **Spring Boot:** add the endpoint with springdoc annotations:
   - a unique `operationId`;
   - a description of what it returns;
   - parameter descriptions;
   - a typed response DTO.
   If the endpoint's records are referred to by a business key that isn't the JPA key (for
   example an employee number), declare that key in ARIA's configuration.
2. **ARIA:** add a thin tool module to the tools folder and register it:
   - a typed function;
   - a docstring (fall back to the OpenAPI summary);
   - an `operationId` binding in deployment configuration.
   No paths, keys or relationships are written in the tool.
3. **Reload schemas.**
   - ARIA validates the tool against OpenAPI and derives its keys and fields from the response
     DTO, `/api/metadata/schema` and any configured business keys (see below).
   - It adds the tool to the key graph and the search index.
   - It reports the tool as ready, or as unavailable with the reason.

### Keys are not always IDs

A key is whatever field identifies a record and is used elsewhere to refer to it. It can have any
name: `empNo`, a division code, a serial number, or several fields together. In the current
backend:

- `Employee`'s JPA key is a surrogate `id`, but attendance, leave and other HR tables refer to
  employees by `empNo`.
- `HrOfficialDetails`, `HrPersonalDetails` and `HrSalaryAllDetails` use `empNo` as their JPA key.
- 3 entities have composite keys (`@EmbeddedId`/`@IdClass`).
- No entity marks its business key (there's no `@NaturalId` or unique constraint).

So ARIA builds its key graph from four declared sources, never from field names:

1. JPA primary keys from `/api/metadata/schema`, including composite key parts.
2. Business keys declared in deployment configuration: entity, field, and the label users know
   it by (today the employee number, via `primary_id_field`).
3. Parameter-to-field bindings in the tool contracts (which response field feeds which
   parameter).
4. Foreign-key references Spring Boot declares. Today it infers them from name similarity, so
   treat those as hints that must be confirmed by sources 2 or 3, never as links on their own.

A key with no declaration is reported as a missing link instead of guessed. Do not change
Spring Boot without an explicit request.

## The models

Measured on the test host on 2026-10-30. Model names and these numbers belong in configuration as a
per-model capability profile, not in code.

| | Tool/routing model | Synthesis model |
|---|---|---|
| Model (config: `MODEL_NAME`, `GENERAL_MODEL_NAME`) | `qwen2.5:7b` (Q4_K_M) | `llama3.1:8b` |
| Context per request on the host | 8,192 tokens | 8,192 tokens |
| Output speed | about 15 tokens/s | about 15 tokens/s |
| Reading an 8k-token prompt | about 8.6 s uncached, 1–2 s when the prefix is cached | similar |

Both models are kept loaded in GPU memory (about 12.7 GB together). The host's 8,192 limit is
a host setting, not a model limit. Prompts above it are silently cut to about 4k tokens and the
system instructions are lost.

What this means for the design:

- **Prompt budget.** Keep each prompt well under the context: aim for about 4k tokens of input,
  leaving room for output. Count tokens before every call, and fail with `context_capacity` rather
  than send an oversized prompt. Set the context length explicitly through an API that honors
  it: the OpenAI-compatible endpoint ignores it, while Ollama's native API accepts `num_ctx`.
  Alternatively, raise the host's `OLLAMA_CONTEXT_LENGTH` if GPU memory allows.
- **Output is the slow part.** At about 15 tokens/s, a 300-token answer takes 20 s. Keep model
  output short. Have code render record lists, tables, trees and charts, and let the model write
  only the narrative and placeholders.
- **Small models follow narrow tasks best.** Give each call one decision with a short schema:
  - enumerate the allowed choices (route values, tool names, source IDs, field names);
  - use structured output with a JSON schema (constrained decoding on Ollama);
  - use a low temperature for routing and tool choice;
  - show at most about 8–10 tools per call.
- **Code does whatever has a correct answer:** key chaining, calculations, rendering and
  validation. Spend model calls only on language decisions.
- **Use the cache.** Keep fixed instructions first and request-specific content last.
- **Re-evaluate on model changes.** When either model changes, rerun the phase 10 evaluation
  set. A stronger model may allow merging steps; a weaker one may need narrower calls.

## Request flow (keep this flow)

The order and outputs of these steps are fixed; how each is implemented is up to you.

```
user prompt
   ├─► 1. Route: RAG, tools, both, or conversation
   ├─► 2. Gazetteer: directory names in the prompt (code only; alongside step 1)
   ├─► 3. Semantic search: top tools + the tools that produce their keys (PK/FK chain)
   ├─► 4. Tool calling: choose tools and arguments, run the key chain (RAG runs alongside)
   └─► 5. Synthesis: answer, tables and charts from the evidence
```

**Before the flow:**
- Validate the JWT and check revocation markers.
- For a saved chat, verify the caller owns it before restoring its history.
- Compact history to the user's prompts plus the tools called (with scalar arguments).
- Filter the tools by the caller's roles.

1. **Route.** A structured decision returns:
   - the route (`rag`, `tools`, `both`, `conversation`);
   - whether the request is in scope;
   - a clarification question if needed.
   Out-of-scope requests get the configured refusal. Recommended: a short constrained call to
   the tool model, or a configured classifier. It may share a call with step 4's tool choice if
   the prompt stays within budget.
2. **Gazetteer.**
   - Match names against the caller-scoped index, built from the directory tool and name field
     in configuration (today: employees).
   - Return candidates only, and keep every candidate for an ambiguous name.
   - Follow-ups without a name use earlier prompts, then earlier tool arguments.
   - "My …" binds to the caller's own record.
3. **Semantic search.**
   - Take the top-K tools from a vector index of the registered tools' names and descriptions
     (embeddings: `bge-m3`).
   - Expand the shortlist with the tools that produce every required key the user didn't give,
     using the key graph.
   - K and the per-call tool limit come from the model profile.
4. **Tool calling.**
   - Recommended for small models: the model picks the goal tool or tools and fills the
     arguments it can take from the user's words (constrained to the shortlist and its
     parameter schemas). Code then resolves the key chain deterministically: it calls the
     producers first, selects the requested subject from their results, and passes the keys on.
   - Return to the model only for genuine language decisions; ask the user when several
     results match.
   - A bounded tool-calling loop is the fallback for open-ended multi-step requests.
   - Either way:
     - key arguments must come from earlier results, the prompt or the caller's identity;
     - independent calls run concurrently, as the calling user;
     - responses are validated against the contract;
     - full rows stay in code;
     - missing evidence is reported as missing.
   - When the route includes RAG, the knowledge retrieval runs in parallel.
5. **Synthesis.**
   - Code packs a compact evidence packet within budget: projections by source ID, knowledge
     passages with references, and numbers calculated in code with provenance.
   - The synthesis model writes a short narrative, plus placeholders for record lists, trees and
     charts, constrained to existing source IDs and fields. Code fills them in.
   - **Graphs and charts** are built in code in the frontend's `ChartPayload` shape: `type`,
     `title`, `labels`, `values` or `series`, axis labels and `dataset_id`; `points` for
     scatter and bubble; `matrix_data` and `y_labels` for heatmaps.
     - Supported types: bar, line, area, pie, doughnut, radar, polarArea, scatter, bubble,
       histogram, heatmap.
     - Pick the type from the data: lines for periods, bars for comparisons, pie/doughnut only
       for parts of a whole.
     - Charts are sent as `chart` events and in `done.charts`.
   - Code checks always run, and every failure reason is traced. Model review is optional. A
     failed draft gets one rewrite with the specific failures; after that, publish only the
     verified parts and say what's missing.

**After the flow:** stream `done` with the fields the frontend reads:
- `answer`;
- `toolCalls` (`[{tool, args, result}]`, masked);
- `results` and `endpointResults`;
- `chart` / `charts`;
- `executionTimeMs`, `serverTimeMs`, `promptTokens`, `completionTokens`, `totalTokens`;
- missing items, verification metadata and the trace ID.

Then save the turn and store the trace. An error at any step ends with an `error` event: the
step, the kind, a safe message, the tool calls so far and the trace ID.

## Implementation guidance (recommended, not required)

- **Orchestration:** an explicit state machine for the flow (for example LangGraph or plain
  async code), with each step a small, separately testable function that emits trace events.
- **Model access:** a provider adapter that can set the context length, structured-output schema,
  temperature, timeout and usage reporting per call, and reads the capability profile from config.
- **Structured outputs:** JSON-schema-constrained responses with enumerations built at runtime
  from the shortlist and evidence.
- **Retrieval:** a vector index of tool descriptions rebuilt on catalog changes; the RAG service
  for documents.
- **Data handling:** typed models for tool results; rows stay in code; projections for models.
- **Testing:** dependency injection for the model, HTTP, Redis and database clients; fake tools for
  universality tests; contract tests against the frontend's TypeScript types.

## Lessons from the previous build

1. The host's context limit was lower than the app assumed, and over-limit prompts lost their
   instructions without any error.
2. Four sequential planning calls (15–25 s each) ran before any data was read, and a full answer
   took about 170 s.
3. The previous answer prose in the history grew every turn; history is now prompts plus tools.
4. Answer checks failed without recording why.
5. One shared planning timeout hid which call stalled.
6. Unbounded Redis retries and eager torch/transformers imports slowed requests and used RAM on an
   8 GB machine.
7. Tests that reached live Redis or Postgres hung. Default tests are offline, and live ones are
   marked.
8. Concurrent agents editing one working tree broke each other's runs. Use one worktree per agent.

## Phases

1. **Skeleton and config.**
   - Settings (env + YAML) with the per-model capability profile, structured logging, the
     service on port 8002, and `/health`.
   - Offline test setup.
   - A preflight that checks config, the model host's context length and the backend's OpenAPI,
     with no model calls.
2. **Auth, chats and history.** JWT, revocation checks, chats in the chats database, ownership
   checks, compacted history.
3. **Tools and key graph.** Load the registered tools from the tools folder, validate them against
   OpenAPI, build the key graph from the four declared key sources ("Keys are not always IDs"),
   and revalidate on reload. Move hardcoded values in existing tool modules into configuration.
   - Tests: fake tools for chaining, a missing producer, a cycle, an unregistered module, and
     adding a tool with no other code change.
   - Key tests:
     - a business key that differs from the JPA key (surrogate `id` plus an employee number);
     - an entity whose JPA key is the business key;
     - a composite key;
     - a key with no "id" in its name;
     - an inferred-only foreign key that must not chain.
4. **Route and gazetteer (steps 1–2).**
   - Tests: ambiguous names, a caller without directory access, field names that look like
     names, follow-ups.
5. **Model adapter.** Context-budget enforcement, structured outputs, usage and cache counters,
   per-call timeouts and traces.
6. **Semantic search (step 3).**
   - Tests: the shortlist always contains the producers of required keys.
7. **Tool calling (step 4)** with code-driven key chaining and the bounded fallback loop.
   - Tests: an invented key is rejected, a chain succeeds, ambiguity asks the user.
8. **Synthesis and charts (step 5).**
   - Tests: every chart type built from calculated data, model numbers never reach a chart, nulls
     versus zeros, incomplete data labelled.
9. **Streaming API and frontend.** Every route and event listed above, plus contract tests. Then
   run ARIA_Frontend against the service and Spring Boot: a chat streams, tool steps show, a
   chart renders.
10. **Evaluation.**
    - Fixture prompts covering: RAG only, tools only, both, key chains, follow-ups, ambiguous
      names, chart requests, and unsupported parts. Compare against independent read-only SQL.
    - Live runs (marked `live`) report time and model calls per step.
    - The add-a-capability test: a new endpoint plus a thin tool, then a reload, and it works.

## Performance targets (live, on the test host)

- A single-tool question: no more than 3 model calls and under 20 s.
- A question needing a key chain: no more than 3 model calls (code runs the chain) and under 30 s.
- A RAG-only question: no more than 2 model calls and under 15 s.
- No model request over the context budget, ever (enforced and tested).
