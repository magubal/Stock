"""
Workspace Monitor — 에이전트 활동 실시간 감시 + 변경 요약
사용법:
    python scripts/workspace_monitor.py                    # 기본 감시 (Stock/ 전체)
    python scripts/workspace_monitor.py --path Test_02     # 특정 경로만
    python scripts/workspace_monitor.py --summary          # 현재까지 변경 요약만 출력
    python scripts/workspace_monitor.py --since 30         # 최근 30분 변경 요약
"""

import sys
import os
import time
import argparse
import hashlib
import difflib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ── 설정 ──────────────────────────────────────────────
IGNORE_PATTERNS = {
    'node_modules', 'venv', '__pycache__', '.git', '.db',
    'package-lock.json', '.pyc', '.pyo', '.egg-info',
    '.claude', '.bkit-memory', '.pdca-snapshots',
}

WATCH_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.md', '.json',
    '.html', '.css', '.txt', '.yaml', '.yml', '.toml',
    '.sql', '.sh', '.bat', '.env',
}

# ── 유틸리티 ──────────────────────────────────────────
def should_watch(path: str) -> bool:
    """감시 대상 여부 판단"""
    p = Path(path)
    for ignore in IGNORE_PATTERNS:
        if ignore in p.parts or path.endswith(ignore):
            return False
    if p.suffix and p.suffix not in WATCH_EXTENSIONS:
        return False
    return True


def get_file_hash(path: str) -> str:
    """파일 해시 (변경 감지용)"""
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except (OSError, PermissionError):
        return ""


def read_file_safe(path: str, max_lines: int = 500) -> list:
    """안전하게 파일 읽기"""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.readlines()[:max_lines]
    except (OSError, PermissionError):
        return []


def get_short_diff(old_lines: list, new_lines: list, max_diff_lines: int = 15) -> str:
    """변경 사항 요약 diff"""
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
    if not diff:
        return ""

    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))

    # 핵심 변경 라인만 추출
    changes = []
    for line in diff[2:]:  # skip --- and +++ headers
        if line.startswith('+') and not line.startswith('+++'):
            changes.append(f"  {line}")
        elif line.startswith('-') and not line.startswith('---'):
            changes.append(f"  {line}")
        if len(changes) >= max_diff_lines:
            changes.append(f"  ... (+{added - max_diff_lines} more)")
            break

    summary = f"(+{added} / -{removed} lines)"
    return f"{summary}\n" + "\n".join(changes)


def classify_change(filepath: str, diff_text: str) -> str:
    """변경 유형 추정"""
    p = Path(filepath)
    name = p.name.lower()
    ext = p.suffix.lower()

    if 'test' in name or 'spec' in name:
        return "테스트"
    if name in ('changelog.md', 'development_log', 'todo.md', 'requests.md'):
        return "문서/로그"
    if 'model' in name or 'schema' in name:
        return "DB/모델"
    if ext in ('.md', '.txt'):
        return "문서"
    if 'api/' in filepath or 'route' in name:
        return "API"
    if 'service' in name:
        return "서비스 로직"
    if ext in ('.jsx', '.tsx', '.css', '.html'):
        return "프론트엔드"
    if ext == '.py':
        return "백엔드/스크립트"
    if ext == '.json':
        return "설정"
    return "기타"


# ── 파일 스냅샷 ──────────────────────────────────────
class FileSnapshot:
    """워크스페이스 파일 상태 스냅샷"""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.files = {}  # path -> {hash, mtime, content}

    def scan(self):
        """전체 스캔"""
        self.files = {}
        for p in self.root.rglob('*'):
            if p.is_file() and should_watch(str(p)):
                path_str = str(p)
                self.files[path_str] = {
                    'hash': get_file_hash(path_str),
                    'mtime': p.stat().st_mtime,
                    'content': read_file_safe(path_str),
                }
        return self

    def diff_against(self, other: 'FileSnapshot') -> dict:
        """다른 스냅샷과 비교하여 변경 사항 반환"""
        changes = {
            'added': [],
            'modified': [],
            'deleted': [],
        }

        for path, info in self.files.items():
            if path not in other.files:
                changes['added'].append(path)
            elif info['hash'] != other.files[path]['hash']:
                changes['modified'].append(path)

        for path in other.files:
            if path not in self.files:
                changes['deleted'].append(path)

        return changes


# ── 변경 이벤트 ──────────────────────────────────────
class ChangeEvent:
    def __init__(self, path: str, change_type: str, timestamp: datetime,
                 old_content: list = None, new_content: list = None):
        self.path = path
        self.change_type = change_type  # added, modified, deleted
        self.timestamp = timestamp
        self.old_content = old_content or []
        self.new_content = new_content or []
        self.category = classify_change(path, "")

    @property
    def rel_path(self):
        """상대 경로"""
        try:
            return str(Path(self.path).relative_to(Path(self.path).parents[3]))
        except (ValueError, IndexError):
            return self.path

    @property
    def diff_summary(self):
        if self.change_type == 'added':
            lines = len(self.new_content)
            return f"(새 파일, {lines} lines)"
        elif self.change_type == 'deleted':
            return "(삭제됨)"
        else:
            return get_short_diff(self.old_content, self.new_content)


# ── 모니터 ──────────────────────────────────────────
class WorkspaceMonitor:
    def __init__(self, root_path: str, poll_interval: int = 5):
        self.root = root_path
        self.poll_interval = poll_interval
        self.events: list[ChangeEvent] = []
        self.snapshot = FileSnapshot(root_path).scan()
        self.start_time = datetime.now()

    def poll_once(self) -> list[ChangeEvent]:
        """한 번 폴링하여 변경 사항 감지"""
        new_snapshot = FileSnapshot(self.root).scan()
        changes = new_snapshot.diff_against(self.snapshot)
        new_events = []
        now = datetime.now()

        for path in changes['added']:
            evt = ChangeEvent(path, 'added', now,
                              new_content=new_snapshot.files[path]['content'])
            new_events.append(evt)

        for path in changes['modified']:
            old_content = self.snapshot.files.get(path, {}).get('content', [])
            new_content = new_snapshot.files[path]['content']
            evt = ChangeEvent(path, 'modified', now,
                              old_content=old_content, new_content=new_content)
            new_events.append(evt)

        for path in changes['deleted']:
            evt = ChangeEvent(path, 'deleted', now,
                              old_content=self.snapshot.files.get(path, {}).get('content', []))
            new_events.append(evt)

        self.snapshot = new_snapshot
        self.events.extend(new_events)
        return new_events

    def run(self):
        """실시간 감시 루프"""
        print(f"{'='*60}")
        print(f"  Workspace Monitor 시작")
        print(f"  감시 경로: {self.root}")
        print(f"  폴링 간격: {self.poll_interval}초")
        print(f"  시작 시간: {self.start_time.strftime('%H:%M:%S')}")
        print(f"  종료: Ctrl+C")
        print(f"{'='*60}\n")

        try:
            while True:
                new_events = self.poll_once()
                for evt in new_events:
                    self._print_event(evt)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print(f"\n{'='*60}")
            print("  모니터 종료. 세션 요약:")
            print(f"{'='*60}")
            self.print_summary()

    def _print_event(self, evt: ChangeEvent):
        """이벤트 실시간 출력"""
        icons = {'added': '+', 'modified': '~', 'deleted': '-'}
        icon = icons.get(evt.change_type, '?')
        ts = evt.timestamp.strftime('%H:%M:%S')

        print(f"[{ts}] [{icon}] [{evt.category}] {evt.rel_path}")
        if evt.diff_summary:
            print(f"         {evt.diff_summary.split(chr(10))[0]}")
        print()

    def print_summary(self, since_minutes: int = None):
        """변경 요약 출력"""
        events = self.events
        if since_minutes:
            cutoff = datetime.now() - timedelta(minutes=since_minutes)
            events = [e for e in events if e.timestamp >= cutoff]

        if not events:
            print("  변경 사항 없음.\n")
            return

        # 카테고리별 그룹핑
        by_category = defaultdict(list)
        for evt in events:
            by_category[evt.category].append(evt)

        total_added = sum(1 for e in events if e.change_type == 'added')
        total_modified = sum(1 for e in events if e.change_type == 'modified')
        total_deleted = sum(1 for e in events if e.change_type == 'deleted')

        print(f"\n  총 변경: {len(events)}건 (추가 {total_added} / 수정 {total_modified} / 삭제 {total_deleted})")
        print(f"  기간: {events[0].timestamp.strftime('%H:%M')} ~ {events[-1].timestamp.strftime('%H:%M')}")
        print()

        for category, cat_events in sorted(by_category.items()):
            print(f"  [{category}] ({len(cat_events)}건)")
            for evt in cat_events:
                icons = {'added': '+', 'modified': '~', 'deleted': '-'}
                icon = icons.get(evt.change_type, '?')
                print(f"    {icon} {evt.rel_path}")
                # 수정된 파일은 변경 규모 표시
                if evt.change_type == 'modified' and evt.diff_summary:
                    first_line = evt.diff_summary.split('\n')[0]
                    print(f"      {first_line}")
            print()

        # 추정 작업 내용
        print("  --- 추정 작업 내용 ---")
        if 'API' in by_category or '서비스 로직' in by_category:
            print("  - 백엔드 API/서비스 작업")
        if '프론트엔드' in by_category:
            print("  - 프론트엔드 UI 작업")
        if 'DB/모델' in by_category:
            print("  - 데이터베이스 모델 변경")
        if '문서' in by_category or '문서/로그' in by_category:
            print("  - 문서/로그 업데이트")
        if '백엔드/스크립트' in by_category:
            print("  - 스크립트/유틸리티 작업")
        print()


# ── 빠른 요약 모드 ──────────────────────────────────
def quick_summary(root_path: str, since_minutes: int = 60):
    """최근 N분간 변경된 파일 요약 (감시 없이)"""
    cutoff = datetime.now() - timedelta(minutes=since_minutes)
    root = Path(root_path)

    changes = []
    for p in root.rglob('*'):
        if p.is_file() and should_watch(str(p)):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime >= cutoff:
                    category = classify_change(str(p), "")
                    rel = str(p.relative_to(root))
                    changes.append((mtime, category, rel))
            except (OSError, PermissionError):
                continue

    if not changes:
        print(f"최근 {since_minutes}분간 변경 사항 없음.")
        return

    changes.sort(key=lambda x: x[0])
    by_category = defaultdict(list)
    for mtime, cat, path in changes:
        by_category[cat].append((mtime, path))

    print(f"{'='*60}")
    print(f"  최근 {since_minutes}분 변경 요약 ({len(changes)}건)")
    print(f"  기간: {changes[0][0].strftime('%H:%M')} ~ {changes[-1][0].strftime('%H:%M')}")
    print(f"{'='*60}\n")

    for category, items in sorted(by_category.items()):
        print(f"  [{category}] ({len(items)}건)")
        for mtime, path in items:
            print(f"    {mtime.strftime('%H:%M')} {path}")
        print()


# ── 메인 ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Workspace Monitor - 에이전트 활동 감시')
    parser.add_argument('--path', default='F:/PSJ/AntigravityWorkPlace/Stock',
                        help='감시할 루트 경로')
    parser.add_argument('--interval', type=int, default=5,
                        help='폴링 간격 (초)')
    parser.add_argument('--summary', action='store_true',
                        help='현재까지 변경 요약만 출력 (감시 안 함)')
    parser.add_argument('--since', type=int, default=60,
                        help='--summary 사용 시 최근 N분 (기본 60)')

    args = parser.parse_args()

    if args.summary:
        quick_summary(args.path, args.since)
    else:
        monitor = WorkspaceMonitor(args.path, args.interval)
        monitor.run()


if __name__ == '__main__':
    main()
