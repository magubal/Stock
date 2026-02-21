(function () {
    window.PROJECT_STATUS_ITEMS = [
        {
            "id": "REQ-001",
            "title": "REQ-001 네이버 블로그 데이터 자동 수집",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "run_blog.py",
                                    "path": "scripts/blog_monitor/run_blog.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "final_body_capture.py",
                                    "path": "scripts/final_body_capture.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "naver_bloger_rss_list.txt",
                                    "path": "data/naver_blog_data/naver_bloger_rss_list.txt",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "블로거 RSS 목록 기반으로 최신 글 자동 수집.",
                                    "done": true
                        },
                        {
                                    "label": "본문 이미지 캡처 및 일자별 저장.",
                                    "done": true
                        },
                        {
                                    "label": "스케줄러 기반 자동 실행.",
                                    "done": true
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-002",
            "title": "REQ-002 아이디어 관리 시스템 (Idea Management)",
            "status": "진행",
            "stage": "진행",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "ideas.py",
                                    "path": "backend/app/api/ideas.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "idea.py",
                                    "path": "backend/app/models/idea.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "IdeaBoard.jsx",
                                    "path": "frontend/src/pages/IdeaBoard.jsx",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "아이디어 수집/태깅/상태 관리.",
                                    "done": false
                        },
                        {
                                    "label": "칸반 보드 기반 협업 처리.",
                                    "done": false
                        },
                        {
                                    "label": "실행 항목(Action Item) 전환 추적.",
                                    "done": false
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-003",
            "title": "REQ-003 Pending Packets Inbox 우선 전환 + 즉시처리 연동",
            "status": "진행",
            "stage": "진행",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "collab.py",
                                    "path": "backend/app/api/collab.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "IdeaBoard.jsx",
                                    "path": "frontend/src/pages/IdeaBoard.jsx",
                                    "description": "Related file"
                        },
                        {
                                    "name": "test_collab_triage.py",
                                    "path": "backend/tests/test_collab_triage.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "Inbox 우선 레이아웃.",
                                    "done": false
                        },
                        {
                                    "label": "우측 즉시처리 패널(분류/담당 AI/기한).",
                                    "done": false
                        },
                        {
                                    "label": "처리결과의 아이디어 보드 반영.",
                                    "done": false
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-004",
            "title": "REQ-004 업황/컨센서스 연동 분석 파이프라인",
            "status": "진행",
            "stage": "진행",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "analyze_with_evidence.py",
                                    "path": "scripts/stock_moat/analyze_with_evidence.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "industry_outlook_service.py",
                                    "path": ".agent/skills/stock-moat/utils/industry_outlook_service.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "fnguide_consensus_client.py",
                                    "path": ".agent/skills/stock-moat/utils/fnguide_consensus_client.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "종목 분석 시 업황 데이터 TTL 기반 재사용.",
                                    "done": false
                        },
                        {
                                    "label": "업황 부재 시 업황 리서치 생성/저장.",
                                    "done": false
                        },
                        {
                                    "label": "컨센서스(매출/영업이익) 연동 및 근거 표시.",
                                    "done": false
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-005",
            "title": "REQ-005 국내상장종목 해자 투자가치 엑셀 데이터 정리",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [],
            "checklist": [
                        {
                                    "label": "기준 엑셀 포맷 정리.",
                                    "done": true
                        },
                        {
                                    "label": "종목코드/종목명 등 핵심 필드 정합화.",
                                    "done": true
                        },
                        {
                                    "label": "분석 파이프라인 입력 데이터 품질 확보.",
                                    "done": true
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-006",
            "title": "REQ-006 Collab-Stock Moat Pipeline + Idea Gate",
            "status": "진행",
            "stage": "진행",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "collab.py",
                                    "path": "backend/app/api/collab.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "mcp_server.py",
                                    "path": "scripts/idea_pipeline/mcp_server.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "test_collab_triage.py",
                                    "path": "backend/tests/test_collab_triage.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "triage 시 stock moat 분석결과 재사용.",
                                    "done": false
                        },
                        {
                                    "label": "무조건 아이디어 등록 방지(게이트 조건 적용).",
                                    "done": false
                        },
                        {
                                    "label": "pass/block 근거 이력 저장.",
                                    "done": false
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-007",
            "title": "REQ-007 일관성 모니터링 핵심 경로 Hard-Block",
            "status": "기획",
            "stage": "기획",
            "owner": "TBD",
            "due": "-",
            "programs": [],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-008",
            "title": "REQ-008 요구사항 계약(REQ Contract) 모니터링 강제",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "requirement_contracts.json",
                                    "path": "config/requirement_contracts.json",
                                    "description": "Related file"
                        },
                        {
                                    "name": "requirement_contract_service.py",
                                    "path": "backend/app/services/requirement_contract_service.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "monitoring_rules.py",
                                    "path": "backend/app/services/monitoring_rules.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-009",
            "title": "REQ-009 일관성 모니터링 명칭 고정 + 누락 강제",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-010",
            "title": "REQ-010 3중 강제 게이트 (브랜치/CI/런타임)",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "consistency-monitoring-gate.yml",
                                    "path": ".github/workflows/consistency-monitoring-gate.yml",
                                    "description": "Related file"
                        },
                        {
                                    "name": "check_entrypoint_monitoring.py",
                                    "path": "scripts/ci/check_entrypoint_monitoring.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "fail_closed_runtime.py",
                                    "path": "scripts/consistency/fail_closed_runtime.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-011",
            "title": "REQ-011 Mini Consistency Batch 데모 검증",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "mini_consistency_batch.py",
                                    "path": "scripts/demo/mini_consistency_batch.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "test_mini_consistency_batch.py",
                                    "path": "backend/tests/test_mini_consistency_batch.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-012",
            "title": "REQ-012 Windows 서버 start/stop 단축 스크립트",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "start_servers.ps1",
                                    "path": "scripts/dev/start_servers.ps1",
                                    "description": "Related file"
                        },
                        {
                                    "name": "stop_servers.ps1",
                                    "path": "scripts/dev/stop_servers.ps1",
                                    "description": "Related file"
                        },
                        {
                                    "name": "dev-server-shortcuts.md",
                                    "path": "docs/ops/dev-server-shortcuts.md",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-013",
            "title": "REQ-013 제조업 BM 하위분류 개선(대시보드)",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-014",
            "title": "REQ-014 WICS 기반 BM 재분류",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-015",
            "title": "REQ-015 Excel 기준소스 + Moat DB 이력관리",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "moat_data.py",
                                    "path": "backend/app/models/moat_data.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "moat_dashboard_service.py",
                                    "path": "backend/app/services/moat_dashboard_service.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "extract_moat_data.py",
                                    "path": "scripts/moat_dashboard/extract_moat_data.py",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-016",
            "title": "REQ-016 매일 19:00 변경감지 갱신 스케줄러",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "scheduled_moat_sync.py",
                                    "path": "scripts/moat_dashboard/scheduled_moat_sync.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "register_moat_sync_task.ps1",
                                    "path": "scripts/dev/register_moat_sync_task.ps1",
                                    "description": "Related file"
                        },
                        {
                                    "name": "unregister_moat_sync_task.ps1",
                                    "path": "scripts/dev/unregister_moat_sync_task.ps1",
                                    "description": "Related file"
                        },
                        {
                                    "name": "moat-sync-scheduler.md",
                                    "path": "docs/ops/moat-sync-scheduler.md",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-017",
            "title": "REQ-017 대시보드 프로젝트 현황/체크리스트 패널",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "index.html",
                                    "path": "dashboard/index.html",
                                    "description": "Related file"
                        },
                        {
                                    "name": "dashboard-core.spec.ts",
                                    "path": "tests/playwright/tests/dashboard-core.spec.ts",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "[x] `dashboard/index.html`에 프로젝트 현황 카드 추가.",
                                    "done": true
                        },
                        {
                                    "label": "[x] 하위 체크리스트 항목 클릭 시 진행상태/체크/다음조치 표시.",
                                    "done": true
                        },
                        {
                                    "label": "[x] REQ-015/016/017 연결 근거를 카드에서 확인 가능하게 구성.",
                                    "done": true
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-018",
            "title": "REQ-018 Dashboard black screen 복구",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-019",
            "title": "REQ-019 전역 변경 가드(Global Change Guard) 강제",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "check_global_change_guard.py",
                                    "path": "scripts/ci/check_global_change_guard.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "check_dashboard_static_integrity.py",
                                    "path": "scripts/ci/check_dashboard_static_integrity.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "check_dashboard_runtime_integrity.py",
                                    "path": "scripts/ci/check_dashboard_runtime_integrity.py",
                                    "description": "Related file"
                        },
                        {
                                    "name": "consistency-monitoring-gate.yml",
                                    "path": ".github/workflows/consistency-monitoring-gate.yml",
                                    "description": "Related file"
                        }
            ],
            "checklist": [],
            "nextAction": "-"
},
        {
            "id": "REQ-020",
            "title": "REQ-020 Pdca Status Sync (PDCA-010)",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "(Plan 없음)",
                                    "path": "(Plan 없음)",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "Pdca Status Sync",
                                    "done": true
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-021",
            "title": "REQ-021 News Intelligence Monitor (PDCA-008)",
            "status": "완료",
            "stage": "완료",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "(Plan 없음)",
                                    "path": "(Plan 없음)",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "News Intelligence Monitor",
                                    "done": true
                        }
            ],
            "nextAction": "-"
},
        {
            "id": "REQ-022",
            "title": "REQ-022 Oracle Earnings Integration & Growth-Adjusted Moat (PDCA-006)",
            "status": "검증",
            "stage": "검증",
            "owner": "TBD",
            "due": "-",
            "programs": [
                        {
                                    "name": "oracle-earnings-integration.plan.md",
                                    "path": "docs/01-plan/features/oracle-earnings-integration.plan.md",
                                    "description": "Related file"
                        }
            ],
            "checklist": [
                        {
                                    "label": "Oracle Earnings Integration & Growth-Adjusted Moat",
                                    "done": false
                        }
            ],
            "nextAction": "-"
}
    ];
})();
