#!/usr/bin/env bash
"""
Scenario Builder Script
Walks data/raw/ directories (or given directory), applies PII redaction,
normalizes events, extracts dependency graph & metadata, and outputs standardized
scenarios into data/scenarios/<id>/.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ingest.loaders import load_raw_jsonl_events, load_raw_csv_metrics, load_raw_spans_json
from backend.ingest.redact import redact_text


def build_scenario_from_raw(scenario_dir: Path, output_dir: Path) -> dict:
    """Build a standardized scenario directory from raw files."""
    scenario_id = scenario_dir.name
    dest_dir = output_dir / scenario_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    events = []

    # 1. Parse JSONL files
    for jsonl_file in scenario_dir.glob("*.jsonl"):
        if jsonl_file.name == "events.jsonl":
            continue
        for ev in load_raw_jsonl_events(jsonl_file):
            events.append(ev)

    # 2. Parse CSV metrics
    for csv_file in scenario_dir.glob("*.csv"):
        for ev in load_raw_csv_metrics(csv_file):
            events.append(ev)

    # 3. Parse span JSON
    for json_file in scenario_dir.glob("*span*.json"):
        for ev in load_raw_spans_json(json_file):
            events.append(ev)

    # 4. Apply PII redaction to all messages and string attrs
    for ev in events:
        if ev.get("message"):
            ev["message"] = redact_text(ev["message"])
        if ev.get("attrs"):
            for k, v in list(ev["attrs"].items()):
                if isinstance(v, str):
                    ev["attrs"][k] = redact_text(v)

    # 5. Sort events chronologically
    events.sort(key=lambda e: e["ts"])

    # Write events.jsonl
    events_path = dest_dir / "events.jsonl"
    with open(events_path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    # Copy / generate graph.json
    raw_graph = scenario_dir / "graph.json"
    if raw_graph.exists():
        with open(raw_graph, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
    else:
        # Infer graph from services
        services = sorted(list({e["service"] for e in events if e.get("service")}))
        graph_data = {"nodes": services, "edges": []}
    with open(dest_dir / "graph.json", "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    # Copy / generate meta.json
    raw_meta = scenario_dir / "meta.json"
    if raw_meta.exists():
        with open(raw_meta, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
    else:
        time_range = [events[0]["ts"], events[-1]["ts"]] if events else []
        meta_data = {
            "id": scenario_id,
            "name": scenario_id.replace("_", " ").title(),
            "time_range": time_range,
            "incident_start": events[int(len(events) * 0.6)]["ts"] if events else "",
            "baseline_end": events[int(len(events) * 0.4)]["ts"] if events else "",
        }
    with open(dest_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2)

    # Copy truth.json if present
    raw_truth = scenario_dir / "truth.json"
    if raw_truth.exists():
        with open(raw_truth, "r", encoding="utf-8") as f:
            truth_data = json.load(f)
        with open(dest_dir / "truth.json", "w", encoding="utf-8") as f:
            json.dump(truth_data, f, indent=2)

    return {
        "scenario_id": scenario_id,
        "event_count": len(events),
        "services": len(graph_data.get("nodes", [])),
    }


def main():
    parser = argparse.ArgumentParser(description="Build standardized scenarios from raw data.")
    parser.add_argument("--raw-dir", default="data/raw", help="Path to raw scenarios directory")
    parser.add_argument("--out-dir", default="data/scenarios", help="Destination scenarios directory")
    args = parser.parse_args()

    raw_path = Path(args.raw_dir)
    out_path = Path(args.out_dir)

    if not raw_path.exists():
        print(f"Raw directory '{raw_path}' does not exist.")
        return

    subdirs = [d for d in raw_path.iterdir() if d.is_dir()]
    if not subdirs:
        print(f"No scenario subdirectories found in '{raw_path}'.")
        return

    print(f"Building scenarios from {raw_path} to {out_path}...")
    for d in sorted(subdirs):
        summary = build_scenario_from_raw(d, out_path)
        print(f" - Built {summary['scenario_id']}: {summary['event_count']} events across {summary['services']} services.")
    print("Scenario build completed.")


if __name__ == "__main__":
    main()
