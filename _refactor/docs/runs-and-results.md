## Runs and results (artifacts policy)

Run artifacts are written under `_refactor/runs/`.
In this repo, **completed runs are intended to be committed** (for paper traceability / reproducible audits).

### Git ignore policy
`_refactor/.gitignore` ignores:
- `reports/`
- `_api_probes/`
- `secrets.json`

### Output directory structure
The runner writes one folder per target:
```
runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/
  results.jsonl
  results.provenance.jsonl
  results.provenance.v2.jsonl
  results.summary.json
  run.manifest.json
  run.invocations.jsonl
```

### File semantics
- `results.jsonl`: minimal rows for fast aggregation.
- `results.provenance.jsonl`: full provenance (v1).
- `results.provenance.v2.jsonl`: full provenance (v2; preferred by dashboards/analysis when present).
- `results.summary.json`: per-target aggregate stats (accuracy, token totals, etc).
- `run.manifest.json`: reproducibility snapshot (suite inputs + target config + `pricing_table` + resolved `pricing_tier` + matched `pricing_rate` row).
- `run.invocations.jsonl`: append-only operational log of each `scripts/run.py` invocation that wrote into this folder (timestamp, submit-only vs live, `--limit`, etc). Useful when terminal history is lost.

### Provenance v2 schema (what’s new vs v1)
`results.provenance.v2.jsonl` keeps the v1 fields (so existing tooling that expects `prompt`, `completion_text`,
`usage`, etc. still works), and adds a few structured fields to unify provenance across providers:

- `schema`, `schema_version`: identifies provenance v2 rows (`llmlog.provenance.v2`, version `2`).
- `event`: one of `attempt` (live-mode call), `submit` (submit-only placeholder), `collect` (collector wrote final result),
  or `recover` (timeout recovery script wrote final result).
- `job`: unified job container:
  - `id`, `kind`, `status`
  - `custom_id` / `index` for batch-style APIs
  - optional `metadata` (e.g. batch create/end timestamps when available)
- `provider_output`: best-effort per-request output identifiers and small provider extras:
  - OpenAI: response id, `service_tier`, `created_at`, `completed_at`, reasoning effort (when present)
  - Google: per-response `responseId` + `thought_signature` (when present)
- `timing_ms_source`: explains what `timing_ms` represents (see below)

### Timing semantics (nuances)
`timing_ms` can mean different things depending on provider + execution mode. In provenance v2, interpret timing using:
- `event` (`attempt|submit|collect|recover`)
- `timing_ms_source` (what the number represents)

- **Live mode** (`scripts/run.py` default): `timing_ms` is client-side wall time for the call (includes polling).
- **OpenAI submit-only**: collectors record `timing_ms` from `created_at → completed_at` when available.
- **Anthropic/Gemini batch submit-only**: providers do not expose per-item latency; we record **batch-level**
  `createTime → endTime` (Google) / `created_at → ended_at` (Anthropic) when available. This is most interpretable when
  batch size is 1; otherwise treat it as a coarse upper bound for items in that batch.

#### `timing_ms_source` values (current)
- `runner.live_wall_ms`: wall time measured by `scripts/run.py` in live mode (includes polling when applicable).
- `openai.submit.http_wall_ms`: wall time of the HTTP submission call for OpenAI `--submit-only` rows (**not** completion latency).
- `openai.created_at_to_completed_at`: OpenAI Responses server-side duration from `created_at` to `completed_at`.
- `google.batch.createTime_to_endTime`: Google batch operation duration from `createTime` to `endTime` (batch-level).
- `anthropic.batch.created_at_to_ended_at`: Anthropic message batch duration from `created_at` to `ended_at` (batch-level).
- `collector.submit_ts_to_ts`: best-effort end-to-end wall time from submit timestamp to collect timestamp (includes queueing
  and any collector delay; used when provider-side job timing isn’t available in the provenance row, e.g. when migrating v1 → v2).
- `v1.timing_ms`: legacy timing value carried through from v1 without a more specific classification.

Practical note: for latency analysis, you typically want `event in {attempt,collect,recover}` and should ignore `event=submit`
unless you specifically care about submission overhead.

### Pricing semantics (nuances)
Pricing is enabled per suite via `pricing_table`. For each target run folder:

- `run.manifest.json` / `results.summary.json` include:
  - `pricing_table`: the YAML path used
  - `pricing_tier`: resolved tier used for matching (e.g. `standard`, `batch`, `flex`, `priority`)
  - `pricing_rate`: the matched rate row snapshot (used for stable recomputation)
- `results.summary.json.stats.cost_*` totals are computed by summing per-attempt token usage from provenance and applying
  `pricing_rate` (see `src/llmlog/pricing/cost.py`).

Important provider nuances in cost calculation:
- **OpenAI cached input**: cached input tokens are a subset of input tokens; we avoid double-counting by charging
  `(input_tokens - cached_tokens)` at the normal input rate, plus cached tokens at the cached-input rate (when present).
- **Anthropic cache tokens**: when present, `cache_creation_input_tokens` and `cache_read_input_tokens` are treated as
  separately billed components and are priced using the cache rates in the pricing table (when present).
- **Google thinking tokens**: Google lists output pricing as “output tokens including thinking”; we treat
  `reasoning_tokens` as additional billed output for Google when the API reports them separately.
- **Cache storage**: some providers list cache storage ($/token/hour); we store rates but do not currently compute
  storage costs in `cost_*` totals.

### Async submission fields (OpenAI)
When running with `scripts/run.py --submit-only`, rows may include:
- `openai_response_id`: the `resp_...` id returned by the Responses API (used for later collection)
- `openai_response_status`: last observed server status (best-effort)
- `parsed_answer`: empty/pending until collection

Suggested terminology used in this repo:
- **Live mode**: blocking/polling run (default `scripts/run.py` behavior)
- **Async mode**: submit-only + collector (`--submit-only` + `scripts/collect_openai_submissions.py`)

To collect pending responses later:
```
python scripts/collect_openai_submissions.py --runs-dir runs
python scripts/collect_openai_submissions.py --runs-dir runs --watch-seconds 60
```

#### Recommended collector settings (practical)
- **Default**: use watch mode (`--watch-seconds 60`) so you don't hammer the API.
- **Large batches**: consider increasing the interval (e.g. 120s) and using `--limit` to cap how many pending ids are collected per run file per pass.
- **Small batches / “wait until done”**: use `--poll` only when you explicitly want the collector to block until each id is terminal.

To recover previously timed-out responses (when an id is present):
```
python scripts/recover_openai_timeouts.py
```

### Export for inspection
To export a provenance file into prompt/response text files:
```
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.v2.jsonl --out reports/exports --limit 50 --no-raw
```

