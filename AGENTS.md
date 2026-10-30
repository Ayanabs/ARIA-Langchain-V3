# Project rules

These rules describe what ARIA must do, not how today's code does it. Any framework, library or
technique is fine as long as these rules hold. `BUILD_PLAN.md` describes the target flow and the
recommended approach.

## Universal by design

- Do not hardcode business behavior, organization-specific values, people, identifiers, entity or field names, tool names, endpoint paths, model choices, or keyword-based intent routing.
- Everything specific comes from four sources:
  - the registered tools (what can be called);
  - Spring Boot's OpenAPI and entity metadata (fields, keys, relationships and authorization);
  - deployment configuration (endpoints, models, model capabilities, limits, directory entity);
  - the prompt database (instructions and user-facing wording).
- Any tool added together with a Spring Boot endpoint must work after a schema reload. It needs only a thin registered tool module and its operation binding (plus configuration if needed), with no changes to routing, search, tool calling, synthesis or chart code. Tests prove this with small fake tools, not production tools.
- Contextual intent comes from structured model decisions or configured classifiers, never from keyword rules.

## Tools and keys

- The tool catalog is the set of explicitly registered tools in the tools folder. A file that isn't registered is not a tool. Never generate tools from OpenAPI or database table names.
- Each tool declares typed parameters and a description of what it returns. Endpoints come from deployment contracts and organization values from configuration, never from the tool's code.
- Validate every tool against Spring Boot's OpenAPI before it can be used. Missing or ambiguous operations, incompatible inputs, absent key fields and dependency cycles keep it unavailable. List unavailable tools in diagnostics with the reason, and never fall back to them. Revalidate on schema reload; a failed reload must not leave stale tools advertised as ready.
- A key is any field that identifies a record and that other records or tool parameters use to refer to it. It can have any name and type (an employee number, a code, a serial number, a composite of several fields), and it is often not the entity's JPA `@Id`. Never assume a key is called `id` or matches a naming pattern.
- Build the key set only from declarations:
  - JPA primary keys, including composite `@EmbeddedId`/`@IdClass` parts;
  - business keys declared in deployment configuration (for example the employee number used across HR tables while `Employee`'s JPA key is a surrogate `id`);
  - parameter-to-field bindings in the tool contracts;
  - foreign-key references Spring Boot declares.
- Chain only through those declarations, never through name similarity or parameter-name guessing. An undeclared key or reference is reported as a missing link.
- A key argument is valid only if its value came from an earlier result in the same request, from the user's prompt, or from the caller's own identity. Reject anything else, with the reason.

## Subjects and the gazetteer

- The gazetteer is an in-memory name index used to notice subject mentions in a prompt. Build it only from the directory tool and name field named in configuration, through authorized lookups. Never seed it with hardcoded names, aliases or salutations; excluded tokens and stop words come from configuration and the schema.
- Scope it to the caller. A user must never learn a name through the gazetteer that their own authorization would not return.
- A match is a candidate mention, not an identity. Keep every candidate for an ambiguous name, resolve identifiers only through authorized lookup results and declared relationships, and ask the user when the choice remains ambiguous. Never choose an identifier from a name match.
- Store only the display name, identifier and source per entry, never full records. Schema field names, tool names and stop words must not become subjects.
- Rebuild it on schema, directory or authorization changes, and record its status in the trace. If it is unavailable, requests still work through lookup tools.
- For follow-ups without a named subject, use names from earlier prompts, then subject arguments of earlier tool calls. Never extract subjects from earlier answer prose.

## Evidence, calculations and answers

- Select the specifically requested subjects from lookup results before using their keys. Never iterate a whole directory to answer a question about selected subjects.
- Keep full rows in code. Models see compact projections with source IDs, and code renders record lists, tables, trees and charts from the real rows.
- Calculate every number in code (counts, totals, changes, groupings), with source, subject and period provenance. Validate the calculation's source, fields, operation, grouping and period before running it.
- Treat record listings and calculations as independent requirements, and keep both for mixed requests.
- Never present totals or charts from truncated data as complete; distinguish unknown completeness from proven completeness. Distinguish empty results, nulls and zeros. Do not invent comparison groups, units, statuses or causal links.
- When part of a request can't be answered, answer the supported parts and name the unsupported ones, rather than inventing an operation or dropping everything.
- Charts use the frontend's chart shape and are built in code from calculated evidence. The model chooses the chart and fields, never the values.
- Code checks on every answer always run: sources exist, numbers match the code's calculations, and no hidden identifiers are shown. Model review of answers is optional (`ARIA_RESPONSE_VALIDATION_ENABLED`). Its state is visible in the response metadata, and it never replaces authorization, subject selection, calculation checks or source bindings.
- Reuse follow-up evidence only while its subject, period, caller authorization, contract and freshness remain valid.

## Models

- Treat model capabilities as configuration, per model: context length, tool-calling support, structured-output support and expected speed. Code adapts to that profile, for example how many tools fit in one call. No model name appears in code.
- Every model request must fit the provider's real per-request context. Count tokens before sending; when a prompt doesn't fit, shrink it structurally or fail with `context_capacity`. Never rely on provider-side truncation, which silently drops the system instructions.
- Send required settings (context length, structured-output schema) through an API that honors them, and verify them at preflight.
- Prefer deterministic code over model calls for anything that has a correct answer, such as key chaining, calculations, rendering and validation. Use models for language decisions: routing, choosing tools and filling arguments from the user's words, and writing the answer.
- Constrain model outputs with schemas and enumerations (route values, tool names, source IDs, field names), so invalid choices are impossible rather than caught later.
- Keep fixed instructions first and request-specific content last, so provider prefix caching can reuse them. Every stateless request still carries its required instructions.
- Give every model call its own timeout and a bounded repair. Traces name the call that failed or stalled.
- Distinguish a local cache of prompt templates from provider KV-prefix caching. Report cache reuse only from provider counters; missing counters mean unknown.
- Keep provider endpoints, credentials, model selection and retry budgets in configuration. Never print secrets, and never treat provider rate-limit delays as application processing time.

## Conversation and observability

- Model-visible history for each earlier turn is the user's prompt plus the tools called, with their scalar arguments. Never resend earlier answers, rows or nested arguments. Compacting history twice must give the same result.
- Trace every request by step. For each model call, record wall time, time to first token, and input, output and cached tokens. For every rejected argument, failed check, rewrite or retry, record the specific reason.
- Preserve conversation context, authorization, evidence validation and traceability whenever routing or response generation changes.

## Infrastructure, tests and code

- Request-path calls to Redis, databases and other services use short timeouts with explicit retry budgets. Document whether each security check fails open or closed.
- Load heavy libraries lazily. Importing the application must stay fast and light on an 8 GB development machine.
- Default tests run offline: no Redis, databases, backend or network, and no telemetry writes. Tests may use live models through the configured, authorized providers; mark them `live` so they run separately. Record live acceptance separately, using only the authorized providers and validation window.
- Verify composite evaluations against independent read-only SQL. Offline checks do not establish live-model acceptance.
- Startup verification must not invent sample subjects, run operational reads or make model calls.
- Write clear, idiomatic code that a human maintainer can follow. Use descriptive names, small focused functions and modules, and avoid dense one-liners, unnecessary abstractions, and comments that restate the code; explain non-obvious decisions instead.
- Several agents may work on this machine. Use a separate git worktree per agent, check the working tree before editing, and preserve unrelated edits made by others.

# Test environment

Development and testing use the servers in `.env`; code always reads addresses from configuration. Never copy credentials out of `.env`.

- Spring Boot backend: `http://192.168.84.190:8080` (`SPRING_BOOT_BASE_URL`)
- Model host: `https://colab.require.help/v1` (`OPENAI_API_BASE`, `GENERAL_OPENAI_API_BASE`); Ollama, with the tool model `qwen2.5:7b` and the synthesis model `llama3.1:8b`, at 8,192 tokens of context per request
- Embeddings: `http://192.168.84.190:11434` (`EMBEDDING_API_BASE`, `bge-m3`)
- RAG search: `http://192.168.84.190:8082/api/search`; NER: `http://192.168.84.190:8009/extract`; cross-encoder: `192.168.84.190:8006`
- Redis: `192.168.84.190:6379`; chats database: `192.168.84.190:5430` (`aria_chats_db`); prompts database: `192.168.84.190:5433` (`aria_prompts_db`)
- ARIA service: port 8002

Default tests stay offline and contact none of these; tests marked `live` may.

# Frontend integration

- The client is ARIA_Frontend at `D:\Work\ACCIMT\Frontend\ARIA_Frontend` (React, Vite, Chart.js). It calls this service through `/api/gateway/*`, which Vite proxies here with the prefix removed.
- Keep its routes, request fields, stream events and response fields compatible. Read `src/lib/chat-stream-manager.ts`, `src/components/chat/types.ts` and `vite.config.ts` before changing an endpoint or event. Do not change the frontend without an explicit request.

# Spring Boot integration

- The backend is at `D:\Work\ACCIMT\Springboot\ARIA_Springboot` (Java sources under `src/main/java/org/accimt/aria`). Read its own project instructions before changing it, and do not change it without an explicit request.
- Use only capabilities Spring Boot already exposes. Do not manufacture endpoints, register evaluation-only readers as production tools, or read its database directly in production code. Report unsupported parts of a request accurately.
- When data or a capability seems missing, check the controllers, DTOs, entities, repositories and services, and confirm the operation, returned fields, keys and authorization in the published OpenAPI and `/api/metadata/schema`. Do not infer an endpoint from a table name or a similar controller.
- Database columns, entity properties, DTO fields and tool parameter names may differ. Bind using declared API fields and relationships, and verify the returned shape before changing a consumer.
- Backend ownership checks, authorization and projection limits are authoritative. A metadata endpoint or generic projection does not prove that a complete dataset is available to the caller.
- A table in `misacc_db_fake`, or a reader defined only for evaluation, does not establish a production tool or a backend endpoint.
- For changes spanning repositories, check each working tree, preserve unrelated edits, and run each project's own checks.

# Current codebase notes

These describe today's code, for agents working on it; they are not requirements for a rebuild.

- Tools live in `aria_agent/tools`, are exported through `aria_agent/tools/legacy_catalog.py` and collected by `aria_agent/tools/__init__.py`. Operation bindings are in `agent_config.yaml` under `python_tool_contracts`, applied by `aria_agent/services/python_tool_contracts.py`.
- Spring Boot publishes entity metadata at `/api/metadata/schema` (`EntityMetadataController`). It marks the JPA `@Id` as the PK, and infers foreign keys from name similarity and a hand-maintained list, so those are not reliable declarations. Business keys are not marked: `Employee`'s JPA key is a surrogate `id`, while related HR tables link by `empNo`. Some HR entities use `empNo` as their JPA key, and 3 entities have composite keys. The current identity configuration (`primary_id_field`) declares the employee business key.
- The model provider is reached through an OpenAI-compatible endpoint, which does not pass ARIA's context length to the host.
