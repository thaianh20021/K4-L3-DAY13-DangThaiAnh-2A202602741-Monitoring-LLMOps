"""Local, read-only dashboard for the six Day 13 log metrics."""

import argparse
import html
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * pct / 100
    lower = int(position)
    return ordered[lower] + (ordered[min(lower + 1, len(ordered) - 1)] - ordered[lower]) * (position - lower)


def load_metrics(path):
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            item["_time"] = datetime.fromisoformat(item["ts"].replace("Z", "+00:00"))
            records.append(item)
    if not records:
        raise ValueError("No log records")
    end = max(item["_time"] for item in records)
    start = end - timedelta(minutes=60)
    records = [item for item in records if start <= item["_time"] <= end]
    by_minute = defaultdict(list)
    for item in records:
        by_minute[item["_time"].replace(second=0, microsecond=0)].append(item)
    received = [item for item in records if item["event"] == "request_received"]
    responses = [item for item in records if item["event"] == "response_sent"]
    failed = [item for item in records if item["event"] == "request_failed"]
    tools = [item for item in responses if item.get("tool_success") is not None]
    latency = [item["latency_ms"] for item in responses if "latency_ms" in item]
    ttft = [item["ttft_ms"] for item in responses if "ttft_ms" in item]
    quality = [item["quality_score"] for item in responses if "quality_score" in item]
    minutes = [start.replace(second=0, microsecond=0) + timedelta(minutes=i) for i in range(61)]

    def series(event, field=None):
        return [
            sum(item.get(field, 0) for item in by_minute[minute] if item["event"] == event)
            if field else sum(item["event"] == event for item in by_minute[minute])
            for minute in minutes
        ]

    return {
        "start": start, "end": end, "requests": len(received),
        "latency": latency, "ttft": ttft, "errors": len(failed),
        "retrieval": 100 * sum(item["tool_success"] is True for item in tools) / len(tools) if tools else 0,
        "cost": sum(item.get("cost_usd", 0) for item in responses),
        "tokens_in": sum(item.get("tokens_in", 0) for item in responses),
        "tokens_out": sum(item.get("tokens_out", 0) for item in responses),
        "quality": statistics.mean(quality) if quality else 0,
        "latency_series": [
            percentile(samples, 95) if samples else None
            for minute in minutes
            for samples in [[item["latency_ms"] for item in by_minute[minute]
                             if item["event"] == "response_sent" and "latency_ms" in item]]
        ],
        "traffic_series": series("request_received"),
        "error_series": series("request_failed"),
        "cost_series": series("response_sent", "cost_usd"),
        "token_series": [
            a + b for a, b in zip(series("response_sent", "tokens_in"),
                                    series("response_sent", "tokens_out"))
        ],
        "quality_series": [
            statistics.mean([item["quality_score"] for item in by_minute[minute]
                             if item["event"] == "response_sent" and "quality_score" in item])
            if any(item["event"] == "response_sent" and "quality_score" in item
                   for item in by_minute[minute]) else None
            for minute in minutes
        ],
    }


def chart(values, color, threshold=None):
    ceiling = max(max((value for value in values if value is not None), default=0),
                  threshold or 0, 0.01) * 1.12
    marks = " ".join(
        f'{"M" if i == 0 or values[i - 1] is None else "L"} {i * 6.5:.1f} {72 - value / ceiling * 64:.1f}'
        for i, value in enumerate(values) if value is not None
    )
    dots = "".join(f'<circle cx="{i * 6.5:.1f}" cy="{72 - value / ceiling * 64:.1f}" r="2" fill="{color}"/>'
                   for i, value in enumerate(values) if value is not None)
    line = ""
    if threshold is not None:
        y = 72 - threshold / ceiling * 64
        line = f'<line x1="0" y1="{y:.1f}" x2="390" y2="{y:.1f}" stroke="#c95742" stroke-dasharray="4 4"/>'
    return (f'<svg viewBox="0 0 390 78" preserveAspectRatio="none" role="img" aria-label="Metric over 60 minutes">'
            f'{line}<path d="{marks}" fill="none" stroke="{color}" stroke-width="2.5"/>{dots}</svg>')


def render(metrics):
    config = yaml.safe_load((ROOT / "config/dashboard.yaml").read_text(encoding="utf-8"))["dashboard"]
    panels = config["panels"]
    p = {item["id"]: item for item in panels}
    threshold = lambda key: p[key]["threshold"]["value"]
    peak = percentile(metrics["latency"], 95)
    error_rate = 100 * metrics["errors"] / metrics["requests"] if metrics["requests"] else 0
    historical = datetime.now(timezone.utc) - metrics["end"] > timedelta(minutes=5)
    label = "Historical replay" if historical else "Live"
    cards = [
        ("latency", f'P50 {percentile(metrics["latency"], 50):.0f} · P95 {peak:.0f} · P99 {percentile(metrics["latency"], 99):.0f} ms',
         f'TTFT P95 {percentile(metrics["ttft"], 95):.0f} ms', "latency_series", "#238a80"),
        ("traffic", f'{metrics["requests"]} requests', f'Peak {max(metrics["traffic_series"])} requests/min',
         "traffic_series", "#3378a4"),
        ("errors", f'{error_rate:.1f}% error rate', f'{metrics["errors"]} failed · retrieval {metrics["retrieval"]:.1f}% success',
         "error_series", "#b94b58"),
        ("cost", f'${metrics["cost"]:.4f} USD', "Sum of response cost by minute", "cost_series", "#9a6a2c"),
        ("tokens", f'{metrics["tokens_in"]:,} in · {metrics["tokens_out"]:,} out', "Tokens per minute",
         "token_series", "#715ba5"),
        ("quality", f'{metrics["quality"]:.2f} / 1.00', "Mean quality proxy by minute",
         "quality_series", "#52865b"),
    ]
    blocks = []
    for key, value, detail, series_key, color in cards:
        panel = p[key]
        unit = html.escape(panel["unit"])
        limit = threshold(key)
        blocks.append(
            f'<section><header><h2>{html.escape(panel["title"])}</h2><span>{unit}</span></header>'
            f'<strong>{html.escape(value)}</strong><p>{html.escape(detail)}</p>'
            f'{chart(metrics[series_key], color, limit if key == "latency" else None)}'
            f'<footer>Threshold: {panel["threshold"]["operator"]} {limit} {unit}</footer></section>'
        )
    start = metrics["start"].astimezone().strftime("%Y-%m-%d %H:%M")
    end = metrics["end"].astimezone().strftime("%H:%M %Z")
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta http-equiv="refresh" content="{config['refresh_seconds']}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day 13 runtime dashboard</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f6f8f9;color:#26343b;font:14px Arial,sans-serif}}
main{{max-width:1300px;margin:auto;padding:20px 24px}}h1{{font-size:23px;margin:0}}
.top{{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid #bccbd0;padding-bottom:16px;margin-bottom:18px}}
.meta{{color:#53666d;text-align:right;line-height:1.5}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}
section{{background:white;border:1px solid #cad6d9;border-radius:5px;padding:17px;min-width:0;height:270px}}
header{{display:flex;justify-content:space-between;gap:8px;align-items:start;height:37px}}
h2{{font-size:15px;margin:0}}header span,footer{{color:#64777f;font-size:11px}}
strong{{display:block;font-size:20px;margin:9px 0 5px}}p{{height:27px;margin:0;color:#53666d;font-size:12px}}
svg{{width:100%;height:94px;margin:7px 0;border-bottom:1px solid #dce5e7}}
footer{{border-top:1px solid #e4eaec;padding-top:8px}}
@media(max-width:850px){{.grid{{grid-template-columns:1fr 1fr}}}}@media(max-width:560px){{.grid{{grid-template-columns:1fr}}.top{{display:block}}.meta{{text-align:left;margin-top:9px}}}}
</style><main><div class="top"><div><h1>Day 13 · Monitoring & LLMOps</h1><div>Runtime dashboard · 6 panels</div></div>
<div class="meta">{label} · 60 min window<br>{start}–{end} · refresh 30s<br>Source: data/logs.jsonl</div></div>
<div class="grid">{''.join(blocks)}</div></main></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        try:
            body = render(load_metrics(ROOT / "data/logs.jsonl")).encode("utf-8")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            self.send_error(500, str(exc))
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        assert percentile([10, 20, 30], 95) == 29
        page = render(load_metrics(ROOT / "data/logs.jsonl"))
        assert page.count("<section>") == 6 and "Historical replay" in page
        print("dashboard self-test passed")
    else:
        HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
