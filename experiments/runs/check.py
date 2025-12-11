import os
import sys
import json
import re
import glob
import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize run provenance for errors, usage, reasoning, and streaming")
    ap.add_argument("--run", dest="run_id", default=os.environ.get("RUN_ID"), help="Run id (e.g., cheap_20251027_2211) or set RUN_ID env")
    args = ap.parse_args()
    run_id = args.run_id
    if not run_id:
        print("Set --run or RUN_ID env")
        sys.exit(1)

    files = glob.glob(f"experiments/runs/*/{run_id}/*/*/*/results.provenance.jsonl")
    pat_rate = re.compile(r"429|rate limit", re.I)
    pat_over = re.compile(r"overloaded|529", re.I)
    pat_quota = re.compile(r"quota|usage limit", re.I)
    pat_timeout = re.compile(r"timeout", re.I)

    def classify(err: str):
        if not err:
            return None
        s = err.lower()
        if pat_rate.search(s):
            return "rate_limit"
        if pat_over.search(s):
            return "overloaded"
        if pat_quota.search(s):
            return "quota"
        if pat_timeout.search(s):
            return "timeout"
        return "other"

    summary = {}

    def add(k):
        if k not in summary:
            summary[k] = {
                "total": 0,
                "ok": 0,
                "errors": 0,
                "rate_limit": 0,
                "overloaded": 0,
                "quota": 0,
                "timeout": 0,
                "other": 0,
                "anth_usage_ok": 0,
                "anth_stream_stop": 0,
                "oai_nothink_minimal": 0,
                "oai_nothink_nonminimal": 0,
                "oai_nothink_missing": 0,
                "oai_think_effort_low": 0,
                "oai_think_effort_medium": 0,
                "oai_think_effort_high": 0,
                "oai_think_effort_other": 0,
            }
        return summary[k]

    for p in files:
        parts = p.split(os.sep)
        try:
            exp, run, provider, model, think = parts[2], parts[3], parts[4], parts[5], parts[6]
        except Exception:
            continue
        S = add((exp, provider, model, think))
        with open(p, "r") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                S["total"] += 1
                err = o.get("error")
                if not err:
                    S["ok"] += 1
                else:
                    S["errors"] += 1
                    cls = classify(err)
                    if cls:
                        S[cls] += 1
                if provider == "anthropic":
                    usage = o.get("usage") or {}
                    if isinstance(usage, dict) and usage.get("input_tokens") is not None:
                        S["anth_usage_ok"] += 1
                    if (o.get("finish_reason") or "").lower() == "stream_stop":
                        S["anth_stream_stop"] += 1
                elif provider == "openai":
                    rr = o.get("raw_response") or {}
                    rrobj = rr.get("response", rr) if isinstance(rr, dict) else {}
                    reasoning = rrobj.get("reasoning") if isinstance(rrobj, dict) else None
                    eff = (reasoning or {}).get("effort") if isinstance(reasoning, dict) else None
                    if think == "nothink":
                        if eff is None:
                            S["oai_nothink_missing"] += 1
                        elif str(eff).lower() == "minimal":
                            S["oai_nothink_minimal"] += 1
                        else:
                            S["oai_nothink_nonminimal"] += 1
                    else:
                        if eff is None:
                            S["oai_think_effort_other"] += 1
                        else:
                            e = str(eff).lower()
                            if e == "low":
                                S["oai_think_effort_low"] += 1
                            elif e == "medium":
                                S["oai_think_effort_medium"] += 1
                            elif e == "high":
                                S["oai_think_effort_high"] += 1
                            else:
                                S["oai_think_effort_other"] += 1

    print(f"RUN={run_id} leaves={len(files)}")

    keys_sorted = sorted(summary.keys())
    if not keys_sorted:
        return
    # Compute fixed widths for first two columns
    w_exp = max(8, max(len(k[0]) for k in keys_sorted))
    def pm_str(k):
        return f"{k[1]}/{k[2]}/{k[3]}"
    w_pm = max(16, max(len(pm_str(k)) for k in keys_sorted))

    # Header
    header_left = f"{'experiment':<{w_exp}}  {'target':<{w_pm}}  metrics"
    print(header_left)
    print("-" * len(header_left))

    for k in keys_sorted:
        v = summary[k]
        exp, prov, model, think = k
        left = f"{exp:<{w_exp}}  {pm_str(k):<{w_pm}}  "
        errs = (
            f"total={v['total']} ok={v['ok']} errors={v['errors']} "
            f"(rate={v['rate_limit']}, over={v['overloaded']}, quota={v['quota']}, timeout={v['timeout']}, other={v['other']})"
        )
        if prov == "anthropic":
            extra = f" anth_usage_ok={v['anth_usage_ok']}/{v['total']} anth_stream_stop={v['anth_stream_stop']}"
        elif prov == "openai":
            if think == "nothink":
                extra = (
                    f" oai_nothink: minimal={v['oai_nothink_minimal']} nonminimal={v['oai_nothink_nonminimal']} missing={v['oai_nothink_missing']}"
                )
            else:
                extra = (
                    f" oai_think: low={v['oai_think_effort_low']} med={v['oai_think_effort_medium']} high={v['oai_think_effort_high']} other={v['oai_think_effort_other']}"
                )
        else:
            extra = ""
        print((left + errs + extra).rstrip())


if __name__ == "__main__":
    main()