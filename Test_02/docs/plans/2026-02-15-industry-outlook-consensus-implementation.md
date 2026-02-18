# Industry Outlook + FnGuide Consensus Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 종목 분석 시 업황(30일 TTL)과 FnGuide 컨센서스를 자동 조회/저장/재사용한다.

**Architecture:** Oracle 저장소를 중심으로 업황과 컨센서스를 캐시 레이어처럼 사용한다. 파이프라인은 기존 해자 분석 경로를 유지하고, 추가 데이터는 보강 정보로 주입한다.

**Tech Stack:** Python, python-oracledb, requests, BeautifulSoup4

---

### Task 1: Continuity Records

**Files:**
- Modify: `REQUESTS.md`
- Create: `docs/plans/2026-02-15-industry-outlook-consensus-design.md`
- Create: `docs/plans/2026-02-15-industry-outlook-consensus-implementation.md`

**Step 1: Add REQ entry**
- REQ-004로 요청/요건/관련 파일 추가

**Step 2: Save design + plan docs**
- 오늘 승인된 설계값 반영

### Task 2: Build Oracle Repository Layer

**Files:**
- Create: `.agent/skills/stock-moat/utils/forecast_repository.py`
- Modify: `.agent/skills/stock-moat/utils/oracle_client.py`

**Step 1: Implement table ensure methods**
- 3개 테이블 create-if-missing

**Step 2: Implement CRUD-like methods**
- get_latest_outlook/save_outlook
- get_latest_consensus/save_consensus
- save_scenarios/get_latest_scenarios

### Task 3: Build Service Clients

**Files:**
- Create: `.agent/skills/stock-moat/utils/industry_outlook_service.py`
- Create: `.agent/skills/stock-moat/utils/fnguide_consensus_client.py`

**Step 1: Industry outlook service**
- TTL 30일 판정 + fallback 생성

**Step 2: FnGuide client**
- HTTP fetch + 파싱 + 정규화 + raw 보관

### Task 4: Integrate Pipeline

**Files:**
- Modify: `scripts/stock_moat/analyze_with_evidence.py`

**Step 1: initialize repository/services**
- Oracle 연결 시 활성

**Step 2: call services during analysis**
- classification 후 업황/컨센서스 조회
- forecast scenarios 저장

**Step 3: include in result payload**
- `industry_outlook`, `consensus_2026`, `forecast_scenarios`

### Task 5: Verification

**Files:**
- Modify if needed: touched files only

**Step 1: compile check**
- `python -m py_compile ...`

**Step 2: runtime check**
- `python scripts/stock_moat/analyze_with_evidence.py --ticker 005930 --name 삼성전자`

**Step 3: output validation**
- oracle/high 유지 여부
- 새 필드 존재 여부
