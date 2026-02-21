import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"f:\PSJ\AntigravityWorkPlace\Stock\Test_02")
PDCA_STATUS = ROOT / "docs" / ".pdca-status.json"
PDCA_ID_MAP = ROOT / "config" / "pdca_id_map.json"

name = "resilient-blog-collector"

# 1. Update id_map
with open(PDCA_ID_MAP, "r", encoding="utf-8") as f:
    id_data = json.load(f)

pdca_id = 26
id_data["map"][name] = pdca_id
id_data["_nextId"] = 27

with open(PDCA_ID_MAP, "w", encoding="utf-8") as f:
    json.dump(id_data, f, indent=2, ensure_ascii=False)
    f.write("\n")

# 2. Update pdca_status
with open(PDCA_STATUS, "r", encoding="utf-8") as f:
    status_data = json.load(f)

plan_path = f"docs/01-plan/features/PDCA-026_{name}.plan.md"

if name not in status_data["features"]:
    status_data["features"][name] = {}
    
status_data["features"][name].update({
    "phase": "plan",
    "planPath": plan_path,
    "startedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
})

if name not in status_data.get("activeFeatures", []):
    status_data.setdefault("activeFeatures", []).append(name)

with open(PDCA_STATUS, "w", encoding="utf-8") as f:
    json.dump(status_data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("Successfully registered PDCA-026.")
