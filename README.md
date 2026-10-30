# ARIA

An organizational data assistant. Rules: `AGENTS.md`. Target flow and phases: `BUILD_PLAN.md`.

## Run

```sh
cp .env.example .env          # then fill in credentials
uv sync
uv run python -m aria preflight   # config, model host context, backend OpenAPI; no model calls
uv run python -m aria serve       # service on HOST:PORT (default 0.0.0.0:8002)
```

## Test

```sh
uv run pytest            # offline: any non-loopback connection fails the test
uv run pytest -m live    # contacts the servers configured in .env
uv run ruff check src tests
```

## Layout

```
config/aria.yaml     deployment config: model capability profiles, limits, backend contract paths
src/aria/
  settings.py        .env + YAML, per-model capability profiles
  logging_setup.py   JSON logs, secret masking, trace IDs
  preflight.py       startup verification (metadata reads only)
  app.py, api/       FastAPI service and routes
  auth/ chats/       phase 2
  catalog/           phase 3: registered tools, OpenAPI validation, key graph
  routing/ gazetteer/  phase 4: steps 1-2
  models/            phase 5: provider adapter
  search/            phase 6: step 3
  calling/           phase 7: step 4
  synthesis/         phase 8: step 5
  streaming/         phase 9: streaming API
tools/               registered tool modules (legacy; reworked in phase 3)
tests/
```
