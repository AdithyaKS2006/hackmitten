import json
import os
from pathlib import Path
from pymongo import ASCENDING, MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "ao03"


def load_all_to_mongo():
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Create indexes
    db.events.create_index([("scenario_id", ASCENDING), ("ts", ASCENDING)])
    db.events.create_index([("scenario_id", ASCENDING), ("service", ASCENDING)])
    db.events.create_index([("id", ASCENDING)])
    db.scenarios.create_index([("id", ASCENDING)], unique=True)
    db.truth.create_index([("scenario_id", ASCENDING)], unique=True)

    scenarios_dir = Path("data/scenarios")
    if not scenarios_dir.exists():
        print("data/scenarios directory not found.")
        return

    for sc_dir in sorted(scenarios_dir.iterdir()):
        if not sc_dir.is_dir():
            continue
        sc_id = sc_dir.name
        print(f"Loading scenario: {sc_id}")

        # Meta & Graph
        meta_file = sc_dir / "meta.json"
        graph_file = sc_dir / "graph.json"
        truth_file = sc_dir / "truth.json"
        events_file = sc_dir / "events.jsonl"

        meta = {}
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

        graph = {"nodes": [], "edges": []}
        if graph_file.exists():
            with open(graph_file, "r", encoding="utf-8") as f:
                graph = json.load(f)

        db.scenarios.update_one(
            {"id": sc_id},
            {
                "$set": {
                    "id": sc_id,
                    "name": meta.get("name", sc_id),
                    "time_range": meta.get("time_range", []),
                    "meta": meta,
                    "graph": graph,
                }
            },
            upsert=True,
        )

        # Truth (separate collection, strictly for evaluation)
        if truth_file.exists():
            with open(truth_file, "r", encoding="utf-8") as f:
                truth = json.load(f)
                truth["scenario_id"] = sc_id
                db.truth.update_one({"scenario_id": sc_id}, {"$set": truth}, upsert=True)

        # Events
        if events_file.exists():
            events_to_insert = []
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        ev = json.loads(line)
                        ev["scenario_id"] = sc_id
                        events_to_insert.append(ev)

            if events_to_insert:
                db.events.delete_many({"scenario_id": sc_id})
                db.events.insert_many(events_to_insert)
                print(f"  Inserted {len(events_to_insert)} events into MongoDB.")

    print("Successfully loaded all scenarios into MongoDB 'ao03'.")


if __name__ == "__main__":
    load_all_to_mongo()
