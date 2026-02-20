"""PDCA Project Status API — REQ/PDCA ID 네임스페이스 분리."""

import json
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/project-status", tags=["project-status"])

_BASE = Path(__file__).resolve().parents[3]  # Test_02/
_PDCA_STATUS = _BASE / "docs" / ".pdca-status.json"
_ARCHIVE_DIR = _BASE / "docs" / "archive"
_ID_MAP_PATH = _BASE / "config" / "pdca_id_map.json"
_REQUESTS_MD = _BASE / "REQUESTS.md"

# Phase → dashboard status mapping
_PHASE_MAP = {
    "plan": "기획",
    "design": "설계",
    "do": "개발중",
    "check": "검증",
    "archived": "완료",
}

# Phase → next action command
_NEXT_ACTION = {
    "plan": "/pdca design {name}",
    "design": "/pdca do {name}",
    "do": "/pdca analyze {name}",
    "check": "/pdca report {name}",
    "archived": "-",
}


def _load_id_map() -> dict:
    """Load or create pdca_id_map.json."""
    if _ID_MAP_PATH.exists():
        return json.loads(_ID_MAP_PATH.read_text(encoding="utf-8"))
    default = {"_comment": "PDCA feature -> fixed ID mapping.", "_nextId": 1, "map": {}}
    _ID_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ID_MAP_PATH.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
    return default


def _save_id_map(id_map: dict):
    _ID_MAP_PATH.write_text(json.dumps(id_map, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_or_assign_id(id_map: dict, feature_name: str) -> int:
    """Get existing ID or assign next available. Never reuse."""
    if feature_name in id_map["map"]:
        return id_map["map"][feature_name]
    num = id_map["_nextId"]
    id_map["map"][feature_name] = num
    id_map["_nextId"] = num + 1
    _save_id_map(id_map)
    return num


_META_PREFIXES = (
    "PDCA Phase", "Feature", "Created", "Source", "Phase", "Status",
    "Date", "Plan Reference", "Project", "Author",
)


def _parse_plan_description(plan_path: str) -> str:
    """Extract descriptive blockquote from plan.md, skipping metadata lines."""
    full = _BASE / plan_path
    if not full.exists():
        return ""
    try:
        summary = ""
        for line in full.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith(">"):
                continue
            text = stripped.lstrip(">").strip()
            if not text:
                continue
            # Extract **Summary**: value
            if text.startswith("**Summary**:"):
                summary = text.split(":", 1)[1].strip()
                continue
            # Skip metadata lines (> Key: or > **Key**: patterns)
            is_meta = False
            for prefix in _META_PREFIXES:
                if text.startswith(f"**{prefix}**:") or text.startswith(f"{prefix}:"):
                    is_meta = True
                    break
            if is_meta:
                continue
            # First non-metadata blockquote = description
            return text
        return summary  # fallback to **Summary** if found
    except Exception:
        return ""


def _build_checklist(feature: dict, phase: str) -> list:
    """Auto-generate checklist from PDCA phase progression with doc links."""
    checks = []
    has_plan = bool(feature.get("planPath"))
    has_design = bool(feature.get("designPath"))
    archived_to = feature.get("archivedTo", "")
    phase_order = ["plan", "design", "do", "check", "archived"]
    phase_idx = phase_order.index(phase) if phase in phase_order else -1

    checks.append({"label": "Plan 문서 작성", "done": has_plan,
                    "link": feature.get("planPath", "")})
    checks.append({"label": "Design 문서 작성", "done": has_design,
                    "link": feature.get("designPath", "")})
    checks.append({"label": "구현 (Do)", "done": phase_idx >= 2, "link": ""})
    checks.append({"label": "Gap Analysis (Check)", "done": bool(feature.get("matchRate")),
                    "link": feature.get("analysisPath", "")})
    checks.append({"label": "Archive", "done": phase == "archived",
                    "link": archived_to})
    return checks


def _load_active_features() -> list:
    """Load real PDCA features from .pdca-status.json (planPath or archivedTo required)."""
    if not _PDCA_STATUS.exists():
        tracked_features = {}
    else:
        data = json.loads(_PDCA_STATUS.read_text(encoding="utf-8"))
        tracked_features = data.get("features", {})

    result = []
    # 1. Existing tracked features
    for name, info in tracked_features.items():
        if not info.get("planPath") and not info.get("archivedTo"):
            continue  # Skip auto-tracked noise
        result.append({"name": name, **info})
        
    # 2. Dynamically scan for undocumented features from docs/*/features/*.md
    dynamic_features = _scan_dynamic_features(tracked_features)
    result.extend(dynamic_features)
    
    return result

def _scan_dynamic_features(tracked: dict) -> list:
    """Scan docs/01-plan/features, 02-design, 03-analysis, 04-report for feature md files not in tracked."""
    docs_dir = _BASE / "docs"
    discovered = {}
    
    # Map of directory pattern to the badge path key it represents
    doc_types = {
        "01-plan/features": "planPath",
        "02-design/features": "designPath",
        "03-analysis/features": "analysisPath",
        "04-report/features": "reportPath"
    }

    for subdir, path_key in doc_types.items():
        target_dir = docs_dir / subdir
        if not target_dir.exists():
            continue
        for md_file in target_dir.glob("*.md"):
            # feature-name.plan.md -> feature-name
            # feature-name.md -> feature-name
            name = md_file.name
            for ext in [".plan.md", ".design.md", ".analysis.md", ".report.md", ".md"]:
                if name.endswith(ext):
                    name = name[:-len(ext)]
                    break
                    
            if name in tracked:
                continue

            rel_path = md_file.relative_to(_BASE).as_posix()
            if name not in discovered:
                discovered[name] = {
                    "phase": "plan",
                    "id": "",
                    "description": "",
                    "checklist": []
                }
            discovered[name][path_key] = rel_path
            
            # If phase is lower than the document found, upgrade it roughly
            if "design" in subdir and discovered[name]["phase"] in ("plan"):
                discovered[name]["phase"] = "design"
            elif "analysis" in subdir and discovered[name]["phase"] in ("plan", "design"):
                discovered[name]["phase"] = "analysis"
            elif "report" in subdir:
                discovered[name]["phase"] = "report"

    res = []
    for name, info in discovered.items():
        res.append({"name": name, **info})
    return res


def _load_archived_features() -> list:
    """Parse archive _INDEX.md files for archived features."""
    if not _ARCHIVE_DIR.exists():
        return []
    result = []
    for index_file in sorted(_ARCHIVE_DIR.glob("*/_INDEX.md")):
        text = index_file.read_text(encoding="utf-8")
        month_dir = index_file.parent.name  # e.g. "2026-02"
        # Parse ### feature-name blocks
        blocks = re.split(r"^### ", text, flags=re.MULTILINE)
        for block in blocks[1:]:  # skip header
            lines = block.strip().split("\n")
            feature_name = lines[0].strip()
            match_rate = None
            for line in lines:
                m = re.search(r"\*\*Match Rate\*\*:\s*([\d.]+)%", line)
                if m:
                    match_rate = float(m.group(1))
            result.append({
                "name": feature_name,
                "phase": "archived",
                "matchRate": match_rate,
                "archivedTo": f"docs/archive/{month_dir}/{feature_name}/",
            })
    return result


def _feature_to_item(feature: dict, pdca_id: int) -> dict:
    """Convert PDCA feature to PROJECT_STATUS_ITEM format."""
    name = feature["name"]
    phase = feature.get("phase", "do")
    status = _PHASE_MAP.get(phase, "개발중")
    match_rate = feature.get("matchRate")
    next_action = _NEXT_ACTION.get(phase, "-").replace("{name}", name)

    title_suffix = ""
    if match_rate is not None and phase == "archived":
        title_suffix = f" ({match_rate}%)"

    description = ""
    plan_path = feature.get("planPath", "")
    if plan_path:
        description = _parse_plan_description(plan_path)

    # Collect available document paths
    documents = {}
    for key, label in [("planPath", "Plan"), ("designPath", "Design"),
                        ("analysisPath", "Analysis"), ("reportPath", "Report")]:
        path = feature.get(key, "")
        if path:
            documents[label] = path
    # Archived features: check archive directory
    archived_to = feature.get("archivedTo", "")
    if archived_to and not documents:
        archive_base = _BASE / archived_to
        if archive_base.exists():
            for md in sorted(archive_base.glob("*.md")):
                for suffix, label in [("plan", "Plan"), ("design", "Design"),
                                       ("analysis", "Analysis"), ("report", "Report")]:
                    if suffix in md.name:
                        documents[label] = f"{archived_to}{md.name}"

    return {
        "id": f"PDCA-{pdca_id:03d}",
        "title": f"PDCA-{pdca_id:03d} {name}{title_suffix}",
        "status": status,
        "stage": phase,
        "owner": "bkit",
        "due": "-",
        "source": "pdca",
        "matchRate": match_rate,
        "description": description,
        "programs": [],
        "checklist": _build_checklist(feature, phase),
        "documents": documents,
        "nextAction": next_action,
    }


@router.get("/pdca")
async def get_pdca_status():
    """PDCA 기능들을 PROJECT_STATUS_ITEMS 형식으로 반환."""
    id_map = _load_id_map()

    # Collect all features (active + archived)
    seen = set()
    all_features = []

    # Active features from .pdca-status.json
    for f in _load_active_features():
        if f["name"] not in seen:
            seen.add(f["name"])
            all_features.append(f)

    # Archived features from _INDEX.md (skip if already in active)
    for f in _load_archived_features():
        if f["name"] not in seen:
            seen.add(f["name"])
            all_features.append(f)

    # Convert to items with stable IDs
    items = []
    for feature in all_features:
        pdca_id = _get_or_assign_id(id_map, feature["name"])
        items.append(_feature_to_item(feature, pdca_id))

    # Sort: 개발중 → 기획/설계/검증 → 완료
    status_order = {"개발중": 0, "검증": 1, "설계": 2, "기획": 3, "완료": 4}
    items.sort(key=lambda x: (status_order.get(x["status"], 9), x["id"]))

    return {"items": items, "meta": {"total": len(items), "source": "pdca-status-sync"}}


def _parse_requests_md() -> dict:
    """Parse REQUESTS.md and extract document links per REQ ID."""
    if not _REQUESTS_MD.exists():
        return {}
    text = _REQUESTS_MD.read_text(encoding="utf-8")
    result = {}
    # Split by ### REQ-XXX sections
    sections = re.split(r"^### (REQ-\d+):", text, flags=re.MULTILINE)
    # sections = ['header', 'REQ-001', 'content1', 'REQ-002', 'content2', ...]
    for i in range(1, len(sections) - 1, 2):
        req_id = sections[i]
        content = sections[i + 1]
        docs = {}
        # Find all backtick-quoted paths that point to docs/
        for m in re.finditer(r"`(docs/[^`]+\.md)`", content):
            path = m.group(1)
            if (_BASE / path).exists():
                label = _classify_doc(path)
                if label:
                    docs[label] = path
        # Also find any other .md doc links (e.g., docs/plans/)
        for m in re.finditer(r"`(docs/[^`]+)`", content):
            path = m.group(1)
            if path.endswith(".md") and (_BASE / path).exists():
                label = _classify_doc(path)
                if label and label not in docs:
                    docs[label] = path
        if docs:
            result[req_id] = docs
    return result


def _classify_doc(path: str) -> str:
    """Classify a doc path as Plan/Design/Analysis/Report.

    Check order matters: 'design' before 'plan' since 'docs/plans/' contains 'plan'.
    """
    name = path.rsplit("/", 1)[-1].lower()  # classify by filename, not directory
    if "design" in name:
        return "Design"
    if "analysis" in name:
        return "Analysis"
    if "report" in name:
        return "Report"
    if "plan" in name:
        return "Plan"
    if "implementation" in name:
        return "Plan"
    return ""


@router.get("/req-docs")
async def get_req_documents():
    """Return document links for REQ items parsed from REQUESTS.md."""
    return _parse_requests_md()


# Allowed file extensions for document reading (security)
_SAFE_EXTENSIONS = (
    ".md", ".txt", ".json", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".yml", ".yaml", ".toml", ".cfg", ".ini",
    ".sh", ".bat", ".ps1", ".sql",
)

# Blocked path segments
_BLOCKED_SEGMENTS = (".env", "node_modules", "__pycache__", ".git/")


@router.get("/document")
async def get_document_content(path: str = Query(..., description="Relative path to document")):
    """Read a project file and return its content."""
    normalized = path.replace("\\", "/")
    # Block path traversal
    if ".." in normalized:
        raise HTTPException(status_code=403, detail="Access denied")
    # Block sensitive paths
    for seg in _BLOCKED_SEGMENTS:
        if seg in normalized:
            raise HTTPException(status_code=403, detail="Access denied")

    full_path = _BASE / normalized
    # Ensure resolved path stays within project
    try:
        full_path.resolve().relative_to(_BASE.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")
    if full_path.suffix not in _SAFE_EXTENSIONS:
        raise HTTPException(status_code=403, detail=f"File type {full_path.suffix} not allowed")

    try:
        content = full_path.read_text(encoding="utf-8")
        return {"path": normalized, "content": content, "lines": len(content.splitlines())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
