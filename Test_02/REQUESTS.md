# 요청 관리 (REQUESTS)

> 마지막 업데이트: 2026-02-19 02:30 by Codex
> 인코딩 표준: UTF-8 (no BOM)

---

## 요청 목록 요약

| 요청 ID | 제목 | 상태 |
|---|---|---|
| REQ-001 | 네이버 블로그 데이터 자동 수집 | 완료 |
| REQ-002 | 아이디어 관리 시스템 (Idea Management) | 진행 |
| REQ-003 | Pending Packets Inbox 우선 전환 + 즉시처리 연동 | 진행 |
| REQ-004 | 업황/컨센서스 연동 분석 파이프라인 | 진행 |
| REQ-005 | 국내상장종목 해자 투자가치 엑셀 데이터 정리 | 완료 |
| REQ-006 | Collab-Stock Moat Pipeline + Idea Gate | 진행 |
| REQ-007 | 일관성 모니터링 핵심 경로 Hard-Block | 기획 |
| REQ-008 | 요구사항 계약(REQ Contract) 모니터링 강제 | 완료 |
| REQ-009 | 일관성 모니터링 명칭 고정 + 누락 강제 | 완료 |
| REQ-010 | 3중 강제 게이트 (브랜치/CI/런타임) | 완료 |
| REQ-011 | Mini Consistency Batch 데모 검증 | 완료 |
| REQ-012 | Windows 서버 start/stop 단축 스크립트 | 완료 |
| REQ-013 | 제조업 BM 하위분류 개선(대시보드) | 완료 |
| REQ-014 | WICS 기반 BM 재분류 | 완료 |
| REQ-015 | Excel 기준소스 + Moat DB 이력관리 | 완료 |
| REQ-016 | 매일 19:00 변경감지 갱신 스케줄러 | 완료 |
| REQ-017 | 대시보드 프로젝트 현황/체크리스트 패널 | 완료 |
| REQ-018 | Dashboard black screen 복구 | 완료 |
| REQ-019 | 전역 변경 가드(Global Change Guard) 강제 | 완료 |
| REQ-020 | Pdca Status Sync (PDCA-010) | 완료 |
| REQ-021 | News Intelligence Monitor (PDCA-008) | 완료 |
| REQ-022 | Oracle Earnings Integration & Growth-Adjusted Moat (PDCA-006) | 검증 |
| REQ-023 | Investment Intelligence Engine (투자 인텔리전스 엔진) (PDCA-007) | 검증 |
| REQ-024 | Idea Management & AI Collaboration System (PDCA-005) | 검증 |
| REQ-025 | Disclosure Monitoring (PDCA-004) | 완료 |
| REQ-026 | Windows 개발 환경에서 포트를 점유하는 좀비 프로세스를 자동 정리하는 유틸리티 (PDCA-012) | 완료 |
| REQ-027 | Plan 없이 구현된 기능도 개발현황 대시보드에 자동 등록되도록 규칙을 명시하는 건 (PDCA-013) | 완료 |
| REQ-028 | 개발현황 상세 패널에 기능 설명 한 줄과 Plan/Design 문서 링크를 표시하여 문맥 파악을 용이하게 한다 (PDCA-014) | 완료 |
| REQ-029 | Disclosure Auto Collect (PDCA-011) | 완료 |
| REQ-030 | PDCA 신규 피처 등록을 코드 레벨로 자동화하여 에이전트 기억 의존도를 0으로 만드는 건 (PDCA-015) | 기획 |
| REQ-031 | stock-research-dashboard (PDCA-003) | 진행 |

---

### REQ-001: 네이버 블로그 데이터 자동 수집
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-001 |
| 상태 | 완료 |

#### 요구사항
1. 블로거 RSS 목록 기반으로 최신 글 자동 수집.
2. 본문 이미지 캡처 및 일자별 저장.
3. 스케줄러 기반 자동 실행.

#### 관련 파일
- `scripts/blog_monitor/run_blog.py`
- `scripts/final_body_capture.py`
- `data/naver_blog_data/naver_bloger_rss_list.txt`

### REQ-002: 아이디어 관리 시스템 (Idea Management)
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-002 |
| 상태 | 진행 |

#### 요구사항
1. 아이디어 수집/태깅/상태 관리.
2. 칸반 보드 기반 협업 처리.
3. 실행 항목(Action Item) 전환 추적.

#### 관련 파일
- `backend/app/api/ideas.py`
- `backend/app/models/idea.py`
- `frontend/src/pages/IdeaBoard.jsx`

### REQ-003: Pending Packets Inbox 우선 전환 + 즉시처리 연동
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-003 |
| 상태 | 진행 |

#### 요구사항
1. Inbox 우선 레이아웃.
2. 우측 즉시처리 패널(분류/담당 AI/기한).
3. 처리결과의 아이디어 보드 반영.

#### 관련 파일
- `backend/app/api/collab.py`
- `frontend/src/pages/IdeaBoard.jsx`
- `backend/tests/test_collab_triage.py`

### REQ-004: 업황/컨센서스 연동 분석 파이프라인
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-004 |
| 상태 | 진행 |

#### 요구사항
1. 종목 분석 시 업황 데이터 TTL 기반 재사용.
2. 업황 부재 시 업황 리서치 생성/저장.
3. 컨센서스(매출/영업이익) 연동 및 근거 표시.

#### 관련 파일
- `scripts/stock_moat/analyze_with_evidence.py`
- `.agent/skills/stock-moat/utils/industry_outlook_service.py`
- `.agent/skills/stock-moat/utils/fnguide_consensus_client.py`

### REQ-005: 국내상장종목 해자 투자가치 엑셀 데이터 정리
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-005 |
| 상태 | 완료 |

#### 요구사항
1. 기준 엑셀 포맷 정리.
2. 종목코드/종목명 등 핵심 필드 정합화.
3. 분석 파이프라인 입력 데이터 품질 확보.

### REQ-006: Collab-Stock Moat Pipeline + Idea Gate
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-006 |
| 상태 | 진행 |

#### 요구사항
1. triage 시 stock moat 분석결과 재사용.
2. 무조건 아이디어 등록 방지(게이트 조건 적용).
3. pass/block 근거 이력 저장.

#### 관련 파일
- `backend/app/api/collab.py`
- `scripts/idea_pipeline/mcp_server.py`
- `backend/tests/test_collab_triage.py`

### REQ-007: 일관성 모니터링 핵심 경로 Hard-Block
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-007 |
| 상태 | 기획 |

#### 범위
- `backend/app/api/*`
- `scripts/idea_pipeline/*`
- `scripts/stock_moat/*`

#### 설계 문서
- `docs/plans/2026-02-15-global-monitoring-guard-design.md`
- `docs/plans/2026-02-15-global-monitoring-guard-implementation.md`

### REQ-008: 요구사항 계약(REQ Contract) 모니터링 강제
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-008 |
| 상태 | 완료 |

#### 관련 파일
- `config/requirement_contracts.json`
- `backend/app/services/requirement_contract_service.py`
- `backend/app/services/monitoring_rules.py`

### REQ-009: 일관성 모니터링 명칭 고정 + 누락 강제
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-009 |
| 상태 | 완료 |

### REQ-010: 3중 강제 게이트 (브랜치/CI/런타임)
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-010 |
| 상태 | 완료 |

#### 관련 파일
- `.github/workflows/consistency-monitoring-gate.yml`
- `scripts/ci/check_entrypoint_monitoring.py`
- `scripts/consistency/fail_closed_runtime.py`

### REQ-011: Mini Consistency Batch 데모 검증
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-011 |
| 상태 | 완료 |

#### 관련 파일
- `scripts/demo/mini_consistency_batch.py`
- `backend/tests/test_mini_consistency_batch.py`

### REQ-012: Windows 서버 start/stop 단축 스크립트
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-012 |
| 상태 | 완료 |

#### 관련 파일
- `scripts/dev/start_servers.ps1`
- `scripts/dev/stop_servers.ps1`
- `docs/ops/dev-server-shortcuts.md`

### REQ-013: 제조업 BM 하위분류 개선(대시보드)
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-013 |
| 상태 | 완료 |

#### 업데이트
- 제조업을 단일 상위 분류로만 묶지 않고 하위 BM 분류로 세분화.

### REQ-014: WICS 기반 BM 재분류
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-014 |
| 상태 | 완료 |

#### 업데이트
- Naver WICS 기준 단일 라벨로 BM 재분류 및 요약 재생성.

### REQ-015: Excel 기준소스 + Moat DB 이력관리
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-015 |
| 상태 | 완료 |

#### 관련 파일
- `backend/app/models/moat_data.py`
- `backend/app/services/moat_dashboard_service.py`
- `scripts/moat_dashboard/extract_moat_data.py`

#### 업데이트
- 가변 비고 파서(2/3/10+ 줄), `bigo_raw` 저장, 전체 재동기화 완료.
- 신규 종목 등록 시 Naver WICS 확인 후 BM 반영.

### REQ-016: 매일 19:00 변경감지 갱신 스케줄러
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-016 |
| 상태 | 완료 |

#### 관련 파일
- `scripts/moat_dashboard/scheduled_moat_sync.py`
- `scripts/dev/register_moat_sync_task.ps1`
- `scripts/dev/unregister_moat_sync_task.ps1`
- `docs/ops/moat-sync-scheduler.md`

### REQ-017: 대시보드 프로젝트 현황/체크리스트 패널
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-017 |
| 상태 | 완료 |

#### 요구사항
1. [x] `dashboard/index.html`에 프로젝트 현황 카드 추가.
2. [x] 하위 체크리스트 항목 클릭 시 진행상태/체크/다음조치 표시.
3. [x] REQ-015/016/017 연결 근거를 카드에서 확인 가능하게 구성.

#### 관련 파일
- `dashboard/index.html`
- `tests/playwright/tests/dashboard-core.spec.ts`

#### 업데이트 (2026-02-19)
- 프로젝트 현황 카드 및 클릭형 상세 패널 구현.
- Playwright 상호작용 회귀 테스트 추가.

### REQ-018: Dashboard black screen 복구
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-018 |
| 상태 | 완료 |

#### 업데이트
- `dashboard/index.html` 파싱 오류(JSX 닫힘/주석-코드 병합) 수정.
- 시장 모니터링 카드/링크 복구.

### REQ-019: 전역 변경 가드(Global Change Guard) 강제
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-019 |
| 상태 | 완료 |

#### 관련 파일
- `scripts/ci/check_global_change_guard.py`
- `scripts/ci/check_dashboard_static_integrity.py`
- `scripts/ci/check_dashboard_runtime_integrity.py`
- `.github/workflows/consistency-monitoring-gate.yml`

#### 업데이트
- 대시보드 변경 시 Playwright 구조화 테스트를 mandatory로 실행.

---

## 메모
- 본 문서는 UTF-8 기준 문서이며, 요청 추적의 단일 기준 문서입니다.
- 추가 요청/변경 시 반드시 이 문서와 개발 로그를 함께 갱신합니다.

### REQ-020: Pdca Status Sync (PDCA-010)
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-020 |
| 상태 | 완료 |
| PDCA Feature | pdca-status-sync |

#### 요구사항
1. Pdca Status Sync

#### 관련 파일
- (Plan 없음)

### REQ-021: News Intelligence Monitor (PDCA-008)
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-021 |
| 상태 | 완료 |
| PDCA Feature | news-intelligence-monitor |

#### 요구사항
1. News Intelligence Monitor

#### 관련 파일
- (Plan 없음)

### REQ-022: Oracle Earnings Integration & Growth-Adjusted Moat (PDCA-006)
| 항목 | 내용 |
|---|---|
| 요청 ID | REQ-022 |
| 상태 | 검증 |
| PDCA Feature | oracle-earnings-integration |

#### 요구사항
1. Oracle Earnings Integration & Growth-Adjusted Moat

#### 관련 파일
- `docs/01-plan/features/oracle-earnings-integration.plan.md`

