from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def _latest_rows_by_id(path: Path) -> Dict[str, Dict[str, Any]]:
    """Return latest JSONL row per `id` from an append-only results file."""
    latest: Dict[str, Dict[str, Any]] = {}
    for row in _iter_jsonl(path):
        rid = row.get("id")
        if rid is None:
            continue
        latest[str(rid)] = row
    return latest


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def _prompt_label_from_template(template_path: Optional[str]) -> str:
    """Derive a short prompt mechanism label from a template file path.

    Example: "prompts/sat_decision__cnf_nl__dpll_alg_linear.j2" -> "dpll_alg_linear"
    """
    if not template_path:
        return "unknown"
    name = Path(str(template_path)).name
    if name.endswith(".j2"):
        name = name[: -len(".j2")]
    parts = [p for p in name.split("__") if p]
    return parts[-1] if parts else name or "unknown"


@dataclass(frozen=True)
class RunInfo:
    suite: str
    run: str
    provider: str
    model: str
    thinking_mode: str
    representation: str
    prompt_template: str
    prompt_label: str
    render_policy: str


def _infer_run_info(*, results_path: Path) -> RunInfo:
    """Infer run metadata from run.manifest.json when available, else from the path."""
    run_dir = results_path.parent
    manifest_path = run_dir / "run.manifest.json"
    if manifest_path.exists():
        m = _read_json(manifest_path)
        prompting = (m.get("prompting") or {}) if isinstance(m, dict) else {}
        suite = str(m.get("suite") or "")
        run = str(m.get("run") or "")
        provider = str(((m.get("target") or {}) if isinstance(m.get("target"), dict) else {}).get("provider") or "")
        model = str(((m.get("target") or {}) if isinstance(m.get("target"), dict) else {}).get("model") or "")
        thinking_mode = str(m.get("thinking_mode") or "")
        representation = str(prompting.get("representation") or "unknown")
        prompt_template = str(prompting.get("template") or "unknown")
        prompt_label = _prompt_label_from_template(prompt_template)
        render_policy = str(prompting.get("render_policy") or "unknown")
        # Defensive: fall back to path segments if any field missing.
        if not suite:
            suite = results_path.parts[-6]
        if not run:
            run = results_path.parts[-5]
        if not provider:
            provider = results_path.parts[-4]
        if not model:
            model = results_path.parts[-3]
        if not thinking_mode:
            thinking_mode = results_path.parts[-2]
        return RunInfo(
            suite=suite,
            run=run,
            provider=provider,
            model=model,
            thinking_mode=thinking_mode,
            representation=representation,
            prompt_template=prompt_template,
            prompt_label=prompt_label,
            render_policy=render_policy,
        )

    # Path fallback: runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.jsonl
    return RunInfo(
        suite=results_path.parts[-6],
        run=results_path.parts[-5],
        provider=results_path.parts[-4],
        model=results_path.parts[-3],
        thinking_mode=results_path.parts[-2],
        representation="unknown",
        prompt_template="unknown",
        prompt_label="unknown",
        render_policy="unknown",
    )


@dataclass
class GroupCounts:
    total: int = 0
    pending: int = 0
    errors: int = 0
    answered: int = 0  # parsed_answer in {0,1} and no error
    unclear: int = 0  # parsed_answer==2 and no error (or missing parsed_answer w/o pending)
    correct: int = 0  # correct==True

    def to_json(self) -> Dict[str, Any]:
        total_nonpending = self.total - self.pending
        completed = self.answered + self.unclear
        acc_nonpending = (self.correct / total_nonpending) if total_nonpending > 0 else None
        acc_completed = (self.correct / completed) if completed > 0 else None
        acc_answered = (self.correct / self.answered) if self.answered > 0 else None
        return {
            "total": self.total,
            "pending": self.pending,
            "errors": self.errors,
            "answered": self.answered,
            "unclear": self.unclear,
            "correct": self.correct,
            "denoms": {
                "nonpending": total_nonpending,
                "completed": completed,
                "answered": self.answered,
            },
            "accuracy": {
                # Includes errors (because denom uses total-pending).
                "nonpending": acc_nonpending,
                # Excludes pending and errors; unclear counts in denom.
                "completed": acc_completed,
                # Excludes pending, errors, and unclear.
                "answered": acc_answered,
            },
        }


def _is_pending(row: Dict[str, Any]) -> bool:
    """Pending = submit-only row that has an OpenAI response id but no parsed answer yet."""
    if row.get("error"):
        return False
    return bool(row.get("openai_response_id") and row.get("parsed_answer") is None)


def _is_error(row: Dict[str, Any]) -> bool:
    return bool(row.get("error"))


def _parsed_int(row: Dict[str, Any]) -> Optional[int]:
    v = row.get("parsed_answer")
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None


def _scan_results_files(runs_dir: Path) -> List[Path]:
    results_files: List[Path] = []
    seen_real: Set[str] = set()
    for p in sorted(runs_dir.glob("**/results.jsonl")):
        try:
            real = str(p.resolve())
        except Exception:
            real = str(p)
        if real in seen_real:
            continue
        seen_real.add(real)
        results_files.append(p)
    return results_files


def build_combined_dashboard_data(
    *,
    runs_dir: str,
    include_suites: Optional[Sequence[str]] = None,
    exclude_suites: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Build aggregated data for the combined dashboard.

    This reads `runs/**/results.jsonl` and uses `run.manifest.json` (when present)
    to label runs with representation/prompt metadata.
    """
    runs = Path(runs_dir).resolve()
    include = {s for s in (include_suites or []) if s}
    exclude = {s for s in (exclude_suites or []) if s}

    groups: Dict[Tuple[str, str, str, str, str, str, int, int, int], GroupCounts] = {}
    # key: (suite, run, provider, model, thinking_mode, prompt_label, representation, maxlen, horn, maxvars)

    files = _scan_results_files(runs)
    for results_path in files:
        info = _infer_run_info(results_path=results_path)
        if include and info.suite not in include:
            continue
        if exclude and info.suite in exclude:
            continue

        latest = _latest_rows_by_id(results_path)
        for row in latest.values():
            meta = row.get("meta") or {}
            if not isinstance(meta, dict):
                meta = {}
            maxvars = _safe_int(meta.get("maxvars"))
            maxlen = _safe_int(meta.get("maxlen"))
            horn = _safe_int(meta.get("horn"))
            if maxvars is None or maxlen is None or horn is None:
                continue
            if horn not in (0, 1):
                continue

            key = (
                info.suite,
                info.run,
                info.provider,
                info.model,
                info.thinking_mode,
                info.prompt_label,
                info.representation,
                maxlen,
                horn,
                maxvars,
            )
            c = groups.get(key)
            if c is None:
                c = GroupCounts()
                groups[key] = c
            c.total += 1
            if _is_pending(row):
                c.pending += 1
                continue
            if _is_error(row):
                c.errors += 1
                continue
            p = _parsed_int(row)
            if p is None or p == 2:
                c.unclear += 1
            else:
                c.answered += 1
            if row.get("correct") is True:
                c.correct += 1

    group_rows: List[Dict[str, Any]] = []
    for (suite, run, provider, model, thinking_mode, prompt_label, representation, maxlen, horn, maxvars), counts in sorted(
        groups.items(),
        key=lambda kv: (kv[0][0], kv[0][1], kv[0][6], kv[0][5], kv[0][7], kv[0][8], kv[0][9]),
    ):
        group_rows.append(
            {
                "suite": suite,
                "run": run,
                "provider": provider,
                "model": model,
                "thinking_mode": thinking_mode,
                "prompt_label": prompt_label,
                "representation": representation,
                "maxlen": maxlen,
                "horn": horn,
                "maxvars": maxvars,
                "counts": counts.to_json(),
            }
        )

    # Unique values for filter dropdowns
    def uniq(vals: Iterable[Any]) -> List[Any]:
        out: List[Any] = []
        seen: Set[Any] = set()
        for v in vals:
            if v in seen:
                continue
            seen.add(v)
            out.append(v)
        return out

    suites = uniq([r["suite"] for r in group_rows])
    runs_ = uniq([r["run"] for r in group_rows])
    reps = uniq([r["representation"] for r in group_rows])
    prompts = uniq([r["prompt_label"] for r in group_rows])
    lens = sorted({int(r["maxlen"]) for r in group_rows})

    payload: Dict[str, Any] = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "runs_dir": str(runs),
            "results_files_scanned": len(files),
            "group_rows": len(group_rows),
        },
        "filters": {
            "suites": suites,
            "runs": runs_,
            "representations": reps,
            "prompt_labels": prompts,
            "maxlens": lens,
        },
        "groups": group_rows,
    }
    return payload


def generate_combined_dashboard_html(*, combined: Dict[str, Any], output_path: str, title: str = "llmlog combined dashboard") -> None:
    """Generate a single-file HTML dashboard with client-side filters + a vars→accuracy plot."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    data_json = json.dumps(combined, ensure_ascii=False)
    # Prevent accidental script tag termination if strings contain '</script>'.
    data_json = data_json.replace("</script>", "<\\/script>")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#f5f7fa;padding:20px}}
    .row{{display:flex;gap:16px;flex-wrap:wrap}}
    .card{{background:#fff;border-radius:10px;padding:16px;margin-bottom:16px;box-shadow:0 2px 4px rgba(0,0,0,.06)}}
    .card h2,.card h3{{margin:0 0 8px 0}}
    .muted{{color:#718096}}
    label{{display:block;font-size:12px;color:#4a5568;margin-bottom:4px}}
    select{{padding:6px 8px;border:1px solid #e2e8f0;border-radius:8px;min-width:220px;background:#fff}}
    .filters{{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end}}
    #chart{{width:980px;max-width:100%;height:520px;border:1px solid #e2e8f0;border-radius:12px;background:#fff}}
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    th,td{{border:1px solid #e2e8f0;padding:8px;text-align:left}}
    th{{background:#f7fafc;position:sticky;top:0}}
    .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}}
    .pill{{display:inline-block;padding:2px 8px;border-radius:999px;background:#edf2f7;color:#2d3748;font-size:12px}}
  </style>
</head>
<body>
  <div class="card">
    <h2>{title}</h2>
    <div class="muted">generated_at: <span class="mono" id="generatedAt"></span> · results_files_scanned: <span class="mono" id="filesScanned"></span></div>
  </div>

  <div class="card">
    <h3>Filters</h3>
    <div class="filters">
      <div>
        <label>Suite</label>
        <select id="fSuite"></select>
      </div>
      <div>
        <label>Run</label>
        <select id="fRun"></select>
      </div>
      <div>
        <label>Representation</label>
        <select id="fRep"></select>
      </div>
      <div>
        <label>Prompt mechanism</label>
        <select id="fPrompt"></select>
      </div>
      <div>
        <label>Horn vs nonhorn</label>
        <select id="fHorn">
          <option value="all">All</option>
          <option value="1">Horn</option>
          <option value="0">Nonhorn</option>
        </select>
      </div>
      <div>
        <label>Maxlen</label>
        <select id="fLen"></select>
      </div>
      <div>
        <label>Accuracy metric</label>
        <select id="fMetric">
          <option value="completed">Correct / (Answered + Unclear)  (excludes pending + errors)</option>
          <option value="answered">Correct / Answered  (excludes pending + errors + unclear)</option>
          <option value="nonpending">Correct / (Total − Pending)  (includes errors)</option>
        </select>
      </div>
    </div>
    <div style="margin-top:10px" class="muted" id="summaryLine"></div>
  </div>

  <div class="card">
    <h3>Accuracy vs number of vars</h3>
    <svg id="chart" viewBox="0 0 980 520" preserveAspectRatio="xMidYMid meet"></svg>
    <div class="muted" style="margin-top:8px">
      Tip: hover points for counts. Accuracy is computed from aggregated counts (not averaging per-run percentages).
    </div>
  </div>

  <div class="card">
    <h3>Rows included (after filters)</h3>
    <div style="overflow:auto;max-height:45vh">
      <table>
        <thead>
          <tr>
            <th>suite</th>
            <th>run</th>
            <th>rep</th>
            <th>prompt</th>
            <th>horn</th>
            <th>maxlen</th>
            <th>maxvars</th>
            <th>acc</th>
            <th>counts</th>
          </tr>
        </thead>
        <tbody id="rowsBody"></tbody>
      </table>
    </div>
  </div>

  <script>
  const DASH = {data_json};

  function uniqSorted(arr) {{
    const s = new Set(arr);
    return Array.from(s).sort();
  }}

  function setOptions(selectEl, values, {{allLabel="All", allowAll=true}}={{}}) {{
    selectEl.innerHTML = "";
    if (allowAll) {{
      const opt = document.createElement("option");
      opt.value = "all";
      opt.textContent = allLabel;
      selectEl.appendChild(opt);
    }}
    for (const v of values) {{
      const opt = document.createElement("option");
      opt.value = String(v);
      opt.textContent = String(v);
      selectEl.appendChild(opt);
    }}
  }}

  function getFilterState() {{
    return {{
      suite: document.getElementById("fSuite").value,
      run: document.getElementById("fRun").value,
      rep: document.getElementById("fRep").value,
      prompt: document.getElementById("fPrompt").value,
      horn: document.getElementById("fHorn").value,
      len: document.getElementById("fLen").value,
      metric: document.getElementById("fMetric").value,
    }};
  }}

  function matches(row, st) {{
    if (st.suite !== "all" && row.suite !== st.suite) return false;
    if (st.run !== "all" && row.run !== st.run) return false;
    if (st.rep !== "all" && row.representation !== st.rep) return false;
    if (st.prompt !== "all" && row.prompt_label !== st.prompt) return false;
    if (st.horn !== "all" && String(row.horn) !== st.horn) return false;
    if (st.len !== "all" && String(row.maxlen) !== st.len) return false;
    return true;
  }}

  function aggByMaxvars(rows) {{
    const by = new Map(); // maxvars -> aggregated counts
    for (const r of rows) {{
      const mv = r.maxvars;
      const c = r.counts;
      const key = mv;
      if (!by.has(key)) {{
        by.set(key, {{
          maxvars: mv,
          total: 0, pending: 0, errors: 0, answered: 0, unclear: 0, correct: 0,
        }});
      }}
      const a = by.get(key);
      a.total += c.total;
      a.pending += c.pending;
      a.errors += c.errors;
      a.answered += c.answered;
      a.unclear += c.unclear;
      a.correct += c.correct;
    }}
    return Array.from(by.values()).sort((a,b) => a.maxvars - b.maxvars);
  }}

  function accuracyFromAgg(a, metric) {{
    if (metric === "answered") {{
      return a.answered > 0 ? (a.correct / a.answered) : null;
    }}
    if (metric === "nonpending") {{
      const denom = a.total - a.pending;
      return denom > 0 ? (a.correct / denom) : null;
    }}
    // completed (default): excludes pending + errors; unclear counts in denom
    const denom = a.answered + a.unclear;
    return denom > 0 ? (a.correct / denom) : null;
  }}

  function fmtPct(x) {{
    if (x === null || x === undefined) return "";
    return (x * 100).toFixed(1) + "%";
  }}

  function renderChart(points) {{
    const svg = document.getElementById("chart");
    svg.innerHTML = "";

    const W = 980, H = 520;
    const M = {{l: 60, r: 20, t: 24, b: 50}};
    const PW = W - M.l - M.r;
    const PH = H - M.t - M.b;

    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y).filter(y => y !== null);
    if (xs.length === 0 || ys.length === 0) {{
      const t = document.createElementNS("http://www.w3.org/2000/svg","text");
      t.setAttribute("x","20"); t.setAttribute("y","40");
      t.setAttribute("fill","#4a5568");
      t.textContent = "No data after filters.";
      svg.appendChild(t);
      return;
    }}

    let xmin = Math.min(...xs), xmax = Math.max(...xs);
    if (xmin === xmax) {{ xmin -= 1; xmax += 1; }}
    const ymin = 0.0, ymax = 1.0;

    const xScale = (x) => M.l + (x - xmin) / (xmax - xmin) * PW;
    const yScale = (y) => M.t + (1 - (y - ymin) / (ymax - ymin)) * PH;

    function line(x1,y1,x2,y2,stroke,width=1) {{
      const el = document.createElementNS("http://www.w3.org/2000/svg","line");
      el.setAttribute("x1",x1); el.setAttribute("y1",y1);
      el.setAttribute("x2",x2); el.setAttribute("y2",y2);
      el.setAttribute("stroke",stroke); el.setAttribute("stroke-width",String(width));
      svg.appendChild(el);
      return el;
    }}

    // axes
    line(M.l, M.t, M.l, H - M.b, "#2d3748", 1.5);
    line(M.l, H - M.b, W - M.r, H - M.b, "#2d3748", 1.5);

    // y ticks
    for (let i=0;i<=10;i++) {{
      const y = i/10;
      const py = yScale(y);
      line(M.l-4, py, M.l, py, "#2d3748", 1);
      const txt = document.createElementNS("http://www.w3.org/2000/svg","text");
      txt.setAttribute("x", String(M.l-8));
      txt.setAttribute("y", String(py+4));
      txt.setAttribute("text-anchor","end");
      txt.setAttribute("font-size","12");
      txt.setAttribute("fill","#2d3748");
      txt.textContent = (y*100).toFixed(0) + "%";
      svg.appendChild(txt);
      // gridline
      line(M.l, py, W - M.r, py, "#e2e8f0", 1);
    }}

    // x ticks at observed x's
    for (const x of uniqSorted(xs)) {{
      const xi = Number(x);
      const px = xScale(xi);
      line(px, H - M.b, px, H - M.b + 5, "#2d3748", 1);
      const txt = document.createElementNS("http://www.w3.org/2000/svg","text");
      txt.setAttribute("x", String(px));
      txt.setAttribute("y", String(H - M.b + 20));
      txt.setAttribute("text-anchor","middle");
      txt.setAttribute("font-size","12");
      txt.setAttribute("fill","#2d3748");
      txt.textContent = String(xi);
      svg.appendChild(txt);
    }}

    // axis labels
    const xl = document.createElementNS("http://www.w3.org/2000/svg","text");
    xl.setAttribute("x", String(M.l + PW/2));
    xl.setAttribute("y", String(H - 12));
    xl.setAttribute("text-anchor","middle");
    xl.setAttribute("font-size","13");
    xl.setAttribute("fill","#2d3748");
    xl.textContent = "maxvars";
    svg.appendChild(xl);

    const yl = document.createElementNS("http://www.w3.org/2000/svg","text");
    yl.setAttribute("x", "16");
    yl.setAttribute("y", String(M.t + PH/2));
    yl.setAttribute("transform", `rotate(-90 16 ${{M.t + PH/2}})`);
    yl.setAttribute("text-anchor","middle");
    yl.setAttribute("font-size","13");
    yl.setAttribute("fill","#2d3748");
    yl.textContent = "accuracy";
    svg.appendChild(yl);

    // polyline path
    const pts = points.filter(p => p.y !== null).sort((a,b)=>a.x-b.x);
    const d = pts.map(p => `${{xScale(p.x)}},${{yScale(p.y)}}`).join(" ");
    const pl = document.createElementNS("http://www.w3.org/2000/svg","polyline");
    pl.setAttribute("points", d);
    pl.setAttribute("fill","none");
    pl.setAttribute("stroke","#3182ce");
    pl.setAttribute("stroke-width","2");
    svg.appendChild(pl);

    // points + tooltips
    for (const p of pts) {{
      const cx = xScale(p.x);
      const cy = yScale(p.y);
      const c = document.createElementNS("http://www.w3.org/2000/svg","circle");
      c.setAttribute("cx", String(cx));
      c.setAttribute("cy", String(cy));
      c.setAttribute("r", "5");
      c.setAttribute("fill", "#2b6cb0");
      const title = document.createElementNS("http://www.w3.org/2000/svg","title");
      title.textContent = `maxvars=${{p.x}} acc=${{fmtPct(p.y)}} (correct=${{p.correct}} answered=${{p.answered}} unclear=${{p.unclear}} errors=${{p.errors}} pending=${{p.pending}} total=${{p.total}})`;
      c.appendChild(title);
      svg.appendChild(c);
    }}
  }}

  function renderTable(rows, metric) {{
    const body = document.getElementById("rowsBody");
    body.innerHTML = "";
    const sorted = rows.slice().sort((a,b) => (a.maxvars - b.maxvars) || (a.maxlen - b.maxlen));
    for (const r of sorted) {{
      const tr = document.createElement("tr");
      const acc = r.counts.accuracy?.[metric] ?? null;
      const counts = r.counts;
      tr.innerHTML = `
        <td class="mono">${{r.suite}}</td>
        <td class="mono">${{r.run}}</td>
        <td><span class="pill">${{r.representation}}</span></td>
        <td><span class="pill">${{r.prompt_label}}</span></td>
        <td>${{r.horn === 1 ? "horn" : "nonhorn"}}</td>
        <td class="mono">${{r.maxlen}}</td>
        <td class="mono">${{r.maxvars}}</td>
        <td class="mono">${{fmtPct(acc)}}</td>
        <td class="mono">c=${{counts.correct}} a=${{counts.answered}} u=${{counts.unclear}} e=${{counts.errors}} p=${{counts.pending}} t=${{counts.total}}</td>
      `;
      body.appendChild(tr);
    }}
  }}

  function refresh() {{
    const st = getFilterState();
    const rows = DASH.groups.filter(r => matches(r, st)).map(r => {{
      // flatten counts for easier aggregation
      const c = r.counts;
      return {{
        ...r,
        counts: {{
          total: c.total, pending: c.pending, errors: c.errors, answered: c.answered, unclear: c.unclear, correct: c.correct,
          accuracy: c.accuracy,
        }}
      }};
    }});

    const agg = aggByMaxvars(rows);
    const pts = agg.map(a => {{
      return {{
        x: a.maxvars,
        y: accuracyFromAgg(a, st.metric),
        ...a,
      }};
    }});

    // summary line
    const tot = agg.reduce((s,a)=>s+a.total,0);
    const pend = agg.reduce((s,a)=>s+a.pending,0);
    const err = agg.reduce((s,a)=>s+a.errors,0);
    const ans = agg.reduce((s,a)=>s+a.answered,0);
    const unc = agg.reduce((s,a)=>s+a.unclear,0);
    const cor = agg.reduce((s,a)=>s+a.correct,0);
    const overall = accuracyFromAgg({{total: tot, pending: pend, errors: err, answered: ans, unclear: unc, correct: cor}}, st.metric);
    document.getElementById("summaryLine").textContent =
      `overall: ${{fmtPct(overall)}} · correct=${{cor}} answered=${{ans}} unclear=${{unc}} errors=${{err}} pending=${{pend}} total=${{tot}} · rows=${{rows.length}}`;

    renderChart(pts);
    renderTable(rows, st.metric);
  }}

  function init() {{
    document.getElementById("generatedAt").textContent = DASH.metadata.generated_at;
    document.getElementById("filesScanned").textContent = String(DASH.metadata.results_files_scanned);

    setOptions(document.getElementById("fSuite"), DASH.filters.suites);
    setOptions(document.getElementById("fRun"), DASH.filters.runs);
    setOptions(document.getElementById("fRep"), DASH.filters.representations);
    setOptions(document.getElementById("fPrompt"), DASH.filters.prompt_labels);
    setOptions(document.getElementById("fLen"), DASH.filters.maxlens.map(String));

    for (const id of ["fSuite","fRun","fRep","fPrompt","fHorn","fLen","fMetric"]) {{
      document.getElementById(id).addEventListener("change", refresh);
    }}
    refresh();
  }}

  init();
  </script>
</body>
</html>
"""

    out.write_text(html, encoding="utf-8")


def generate_combined_dashboard(
    *,
    runs_dir: str,
    output_path: str,
    title: str = "llmlog combined dashboard",
    include_suites: Optional[Sequence[str]] = None,
    exclude_suites: Optional[Sequence[str]] = None,
) -> None:
    combined = build_combined_dashboard_data(
        runs_dir=runs_dir,
        include_suites=include_suites,
        exclude_suites=exclude_suites,
    )
    generate_combined_dashboard_html(combined=combined, output_path=output_path, title=title)


