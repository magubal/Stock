import sys, json, os
from pathlib import Path
sys.path.insert(0, str(Path('./backend').resolve()))
from app.api.project_status import _load_active_features, _load_archived_features

features = _load_active_features() + _load_archived_features()

print(json.dumps([f['name'] for f in features if '026' in f['name'] or '027' in f['name']], indent=2))
