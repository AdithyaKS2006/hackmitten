import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional
from backend.models import Event

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "ao03"

_mongo_client = None
_mongo_available: Optional[bool] = None
_last_mongo_check: float = 0.0
MONGO_RETRY_INTERVAL = 5.0  # Retry connection every 5s if failed
_audit_lock = threading.Lock()
_events_cache: dict[str, list[dict[str, Any]]] = {}


def get_mongo_client():
    global _mongo_client, _mongo_available, _last_mongo_check
    now = time.time()
    # If connection was previously marked unavailable, retry after MONGO_RETRY_INTERVAL
    if _mongo_available is False and (now - _last_mongo_check) < MONGO_RETRY_INTERVAL:
        return None

    if _mongo_client is not None:
        try:
            _mongo_client.admin.command("ping")
            return _mongo_client
        except Exception:
            _mongo_client = None
            _mongo_available = False
            _last_mongo_check = now
            return None

    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        _mongo_client = client
        _mongo_available = True
        return _mongo_client
    except Exception:
        _mongo_available = False
        _mongo_client = None
        _last_mongo_check = now
        return None


def get_storage_mode() -> str:
    """Return 'mongo' if MongoDB is accessible, else 'file'."""
    client = get_mongo_client()
    return "mongo" if client is not None else "file"


def list_scenarios() -> list[dict[str, Any]]:
    """List available scenarios with id, name, and time_range."""
    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            scenarios = list(db.scenarios.find({}, {"_id": 0, "id": 1, "name": 1, "time_range": 1}))
            if scenarios:
                return scenarios
        except Exception:
            pass

    # File fallback
    scenarios_dir = Path("data/scenarios")
    results = []
    if scenarios_dir.exists():
        for d in sorted(scenarios_dir.iterdir()):
            if d.is_dir():
                meta_file = d / "meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            results.append({
                                "id": meta.get("id", d.name),
                                "name": meta.get("name", d.name),
                                "time_range": meta.get("time_range", []),
                            })
                    except Exception:
                        pass
    return results


def get_scenario_meta(id: str) -> Optional[dict[str, Any]]:
    """Get metadata for a scenario."""
    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            sc = db.scenarios.find_one({"id": id}, {"_id": 0})
            if sc and "meta" in sc:
                return sc["meta"]
            elif sc:
                return sc
        except Exception:
            pass

    meta_file = Path("data/scenarios") / id / "meta.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_scenario_graph(id: str) -> dict[str, Any]:
    """Get dependency graph for a scenario."""
    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            sc = db.scenarios.find_one({"id": id}, {"_id": 0, "graph": 1})
            if sc and "graph" in sc:
                return sc["graph"]
        except Exception:
            pass

    graph_file = Path("data/scenarios") / id / "graph.json"
    if graph_file.exists():
        with open(graph_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nodes": [], "edges": []}


def get_events(id: str, as_of: Optional[str] = None) -> list[Event]:
    """Get events for scenario id, optionally filtered by ts <= as_of."""
    mode = get_storage_mode()
    raw_events: list[dict[str, Any]] = []

    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            query: dict[str, Any] = {"scenario_id": id}
            if as_of:
                query["ts"] = {"$lte": as_of}
            cursor = db.events.find(query, {"_id": 0}).sort("ts", 1)
            raw_events = list(cursor)
        except Exception:
            raw_events = []

    if not raw_events:
        events_file = Path("data/scenarios") / id / "events.jsonl"
        if events_file.exists():
            mtime = events_file.stat().st_mtime
            cached = _events_cache.get(id)
            if cached and cached.get("mtime") == mtime:
                all_parsed: list[Event] = cached.get("events", [])
            else:
                all_parsed = []
                with open(events_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                ev_dict = json.loads(line)
                                clean_ev = {k: v for k, v in ev_dict.items() if k != "scenario_id"}
                                all_parsed.append(Event(**clean_ev))
                            except Exception:
                                pass
                _events_cache[id] = {"mtime": mtime, "events": all_parsed}

            if as_of:
                return [e for e in all_parsed if e.ts <= as_of]
            return all_parsed

    parsed: list[Event] = []
    for ev in raw_events:
        clean_ev = {k: v for k, v in ev.items() if k != "scenario_id"}
        try:
            parsed.append(Event(**clean_ev))
        except Exception:
            pass
    return parsed


def get_evidence(evidence_id: str, scenario: Optional[str] = None) -> list[dict[str, Any]]:
    """Retrieve raw event or anomaly record matching evidence_id."""
    results = []
    mode = get_storage_mode()

    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            query: dict[str, Any] = {"id": evidence_id}
            if scenario:
                query["scenario_id"] = scenario
            doc = db.events.find_one(query, {"_id": 0})
            if doc:
                return [{k: v for k, v in doc.items() if k != "scenario_id"}]
        except Exception:
            pass

    # Search scenario files
    scenarios = [scenario] if scenario else [d.name for d in Path("data/scenarios").iterdir() if d.is_dir()]
    for sc in scenarios:
        events_file = Path("data/scenarios") / sc / "events.jsonl"
        if events_file.exists():
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        ev = json.loads(line)
                        if ev.get("id") == evidence_id:
                            results.append(ev)
                            return results
    return results


def save_evaluation(eval_dict: dict[str, Any]) -> None:
    """Save evaluation results to MongoDB evaluations collection and cached file."""
    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            db.evaluations.insert_one(eval_dict.copy())
        except Exception:
            pass

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    with open(data_dir / "evaluation.json", "w", encoding="utf-8") as f:
        json.dump(eval_dict, f, indent=2)


def get_evaluation() -> Optional[dict[str, Any]]:
    """Get the latest evaluation output."""
    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            latest = db.evaluations.find_one({}, {"_id": 0}, sort=[("_id", -1)])
            if latest:
                return latest
        except Exception:
            pass

    eval_file = Path("data/evaluation.json")
    if eval_file.exists():
        try:
            with open(eval_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def audit(entry: dict[str, Any]) -> None:
    """Audit log entry to MongoDB and logs/audit.jsonl."""
    # Thread-safe append to logs/audit.jsonl
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    with _audit_lock:
        with open(log_dir / "audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            db.audit_log.insert_one(entry.copy())
        except Exception:
            pass


def get_truth(id: str) -> Optional[dict[str, Any]]:
    """Ground truth for evaluation ONLY. Never called by detect/ or rank/."""
    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            doc = db.truth.find_one({"scenario_id": id}, {"_id": 0})
            if doc:
                return {k: v for k, v in doc.items() if k != "scenario_id"}
        except Exception:
            pass

    truth_file = Path("data/scenarios") / id / "truth.json"
    if truth_file.exists():
        with open(truth_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def ingest_events(scenario_id: str, events: list[dict[str, Any]]) -> int:
    """Ingest live telemetry events into scenario store and invalidate cache."""
    if not events:
        return 0

    mode = get_storage_mode()
    if mode == "mongo":
        try:
            client = get_mongo_client()
            db = client[DB_NAME]
            docs = []
            for ev in events:
                doc = ev.copy()
                doc["scenario_id"] = scenario_id
                docs.append(doc)
            db.events.insert_many(docs)
        except Exception:
            pass

    # Append to scenario events.jsonl
    sc_dir = Path("data/scenarios") / scenario_id
    sc_dir.mkdir(parents=True, exist_ok=True)
    events_file = sc_dir / "events.jsonl"
    with open(events_file, "a", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    # Invalidate in-memory cache for this scenario
    _events_cache.pop(scenario_id, None)
    return len(events)
