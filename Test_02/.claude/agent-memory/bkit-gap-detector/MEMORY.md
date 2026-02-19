# Gap Detector Agent Memory

## Project: Stock Research ONE

### Completed Analyses

1. **stock-moat-estimator** (2026-02-09)
   - Match Rate: 98.4% (PASS)
   - Design doc: `docs/02-design/features/stock-research-dashboard.design.md`
   - Analysis: `docs/03-analysis/features/stock-moat-estimator.analysis.md`
   - Key finding: Implementation exceeds design by +12 scripts
   - Action items: Move DART API key to env vars, expand KSIC mapping table

2. **evidence-based-moat** (2026-02-09, RE-RUN)
   - Match Rate: 95.2% (PASS) -- was 88.5% in v1.0
   - Design doc: `docs/02-design/features/evidence-based-moat.design.md`
   - Analysis: `docs/03-analysis/evidence-based-moat.analysis.md`
   - 82 items checked: 71 matched, 8 partial, 3 missing
   - 5 gaps fixed: excel_io v2 columns, segment_revenue CFS+text, pytest 30 tests, retry 3x, batch processing
   - 12 remaining gaps all Low/Negligible impact
   - Added features: ai_verifier.py, expanded KSIC 100+, multi-year financials, text segment extraction
   - Ready for: `/pdca report evidence-based-moat`

3. **stock-research-dashboard** (2026-02-11, RE-RUN v2.0)
   - Match Rate: 96.3% (PASS) -- was 91.6% in v1.0
   - Design doc: `docs/02-design/features/stock-research-dashboard.design.md`
   - Analysis: `docs/03-analysis/features/stock-research-dashboard.analysis.md`
   - 107 items checked: 103 matched, 3 partial/changed, 1 missing
   - v1->v2 fixes: context_analysis router activated, volatility alert added, error_code+timestamp added, sentiment query optimized
   - 14 added features (positive): DI pattern, env baseURL, _raise_with_code, HTTPException re-raise, etc.
   - Remaining: HTTP 503 (Low), sell signal trend vs absolute (Medium), calculate_trend (Low)
   - Error handling improved 55.6% -> 77.8%
   - Ready for: `/pdca report stock-research-dashboard`

4. **disclosure-monitoring** (2026-02-14, RE-RUN v2.0 on 2026-02-19)
   - Match Rate: 96.4% (PASS) -- same score, deeper analysis
   - Design doc: `docs/02-design/features/disclosure-monitoring.design.md`
   - Analysis: `docs/03-analysis/features/disclosure-monitoring.analysis.md`
   - 103 items checked: 97 matched, 5 changed, 0 missing, 1 partial, 27 added
   - Pipeline: KIND collector -> analyzer (722 lines, deep enrichment) -> JSON -> React CDN frontend
   - v1->v2 corrections: dashboard link is monitoring-link card (not header-actions button), detail field IS populated for 44/1007 records (not empty), Excel fallback reclassified CHANGED not MISSING
   - Key gaps: EUC-KR vs UTF-8 (Medium), dilution_total->dilution_count (Low), detail field not rendered in frontend (Low)
   - 27 added features: 6 taxonomy keywords, earnings YoY enrichment, contract amount enrichment, correction diff analysis, filter bar, cluster click, DataSourceFooter, etc.
   - Error handling: 8/8 (100%), Cross-consistency: 95%, Success criteria: 4/4
   - Ready for: `/pdca report disclosure-monitoring`

5. **liquidity-stress-monitor** (2026-02-14)
   - Match Rate: 97.8% (PASS)
   - Design doc: `docs/02-design/features/liquidity-stress-monitor.design.md`
   - Analysis: `docs/03-analysis/features/liquidity-stress-monitor.analysis.md`
   - 113 items checked: 108 matched, 5 partial, 0 missing
   - Full-stack: 5 DB tables + 2 API endpoints + 8 scripts + 2 dashboard pages
   - Key gaps: News Top 5 shows only Top 1 (Minor), levelColor added (Positive), history enriched (Positive)
   - 11 positive additions: DI, error codes, query validation, React.memo, responsive, etc.
   - Stress calc verified: 6-module weights, normalization ranges, level mapping all exact match
   - Cross-consistency verified: model schemas, level configs, config constants across all files
   - Ready for: `/pdca report liquidity-stress-monitor`

6. **crypto-trends-monitor** (2026-02-14)
   - Match Rate: 96.3% (PASS)
   - Design doc: `docs/02-design/features/crypto-trends-monitor.design.md`
   - Analysis: `docs/03-analysis/features/crypto-trends-monitor.analysis.md`
   - 95 items checked: 85 matched, 7 partial, 0 missing
   - Frontend-only MVP: React CDN + 3 external APIs (CoinGecko, DefiLlama, Fear&Greed) + 2 manual localStorage inputs
   - Key changes: gauge minmax 130->145px, mobile breakpoint 768->900px, trigger thresholds use fixed values vs statistical percentiles
   - 13 positive additions: Fear&Greed 8th gauge, gauge click modal system, regime-colored banner, Promise.allSettled, [행동] tag
   - All 4 trigger engines match design logic; summary generation 100% match across all 4 cards
   - Zero missing features -- all Phase 1 MVP items implemented
   - Ready for: `/pdca report crypto-trends-monitor`

7. **idea-ai-collaboration** (2026-02-14, RE-RUN v2.0)
   - Match Rate: 96.2% (PASS) -- was 93.8% in v1.0
   - Design doc: `docs/02-design/features/idea-ai-collaboration.design.md`
   - Analysis: `docs/03-analysis/features/idea-ai-collaboration.analysis.md`
   - 191 items checked: 175 matched, 11 changed, 5 missing (Phase 3 optional), 19 added
   - 3-phase feature: Core Pipeline (models+API+parsers+CLI) + AI Collab (MCP+protocol) + Dashboard
   - v1.0 Critical bug FIXED: MCP create_idea_from_insights now uses `content=thesis` (was `description=thesis`)
   - Phase 2 Intelligence Layer fully analyzed: CrossModuleService, cross_module API, MCP briefing, events, sector momentum, custom sources, Intelligence Dashboard
   - 19 positive additions: content_hash, 36 category aliases, dry-run, session CRUD, CrossModuleService, Intelligence Dashboard (428 lines), sector momentum, event calendar, custom sources plugin, etc.
   - All 6 DB tables, 23 API endpoints, 8 MCP tools, 4 MCP resources, 3 protocol docs, 10 routers
   - Phase 3 items (idea_connections, idea_outcomes) not started -- "Should" priority, excluded from score
   - Ready for: `/pdca report idea-ai-collaboration`

8. **investment-intelligence-engine** (2026-02-15)
   - Match Rate: 98.5% (PASS)
   - Design doc: `docs/02-design/features/investment-intelligence-engine.design.md`
   - Analysis: `docs/03-analysis/features/investment-intelligence-engine.analysis.md`
   - 116 items checked: 116 matched, 0 missing, 3 Low-impact changes, 12 positive additions
   - 3-layer engine: Signal Rules -> SignalDetectionEngine -> StrategistService + GapAnalyzer
   - Full-stack: 1 DB table + 7 API endpoints + 3 services + 6 MCP tools + 2 MCP resources + dashboard rewrite
   - Zero missing features -- highest fidelity analysis to date
   - 12 added features: duplicate prevention, crypto file fallback, risk keyword counter, category_filter, extra operators, error handling
   - Cross-consistency verified: Model<->Schema<->API 18/18 fields, confidence colors 4/4, rules 5/5
   - Error handling: 9/9 (100%) -- best in project history
   - Ready for: `/pdca report investment-intelligence-engine`

9. **dashboard-project-panel-v2** (2026-02-19)
   - Match Rate: 100% (PASS) -- 12/12 V-XX criteria all PASS
   - Design doc: `docs/02-design/features/dashboard-project-panel-v2.design.md`
   - Analysis: `docs/03-analysis/features/dashboard-project-panel-v2.analysis.md`
   - Scope: 3 files (dashboard/index.html, dashboard/project_status.html, tests/playwright/tests/dashboard-core.spec.ts)
   - UI overhaul: 4-column KPI + full list -> progress bar + badge row + active-card grid + view-all link
   - Detail page: owner/due/nextAction hidden when empty, empty checklist shows message, autoLabel() for extensions
   - All 18+ old CSS classes confirmed removed, no new external libraries added
   - Responsive breakpoint 640px->768px (intentional, consistent with rest of dashboard)
   - Ready for: `/pdca report dashboard-project-panel-v2`

10. **news-intelligence-monitor** (2026-02-19)
   - Match Rate: 98.4% (PASS) -- 19/19 V-XX criteria all PASS
   - Design doc: `docs/02-design/features/news-intelligence-monitor.design.md`
   - Analysis: `docs/03-analysis/features/news-intelligence-monitor.analysis.md`
   - 95 items checked: 92 matched, 2 changed, 0 missing, 6 added
   - Full pipeline: Finviz HTML parser -> SQLite DB -> Claude AI analyzer -> FastAPI 2 endpoints -> React CDN dashboard
   - 14 files: 2 DB models, 4 scripts (config+fetch+analyzer+batch), service+router+main, dashboard+index, seed, playwright
   - Key gaps: 404 response double-nesting (Low), UniqueConstraint name cosmetic (Negligible)
   - 6 positive additions: .env key loader, ensure_tables(), 3-level HTML fallback, DI pattern, 500 error wrapper, Korean sentiment labels
   - Cross-consistency: 15/15 model-schema-API fields, 7/7 config constants, 5/5 sentiment levels, 6/6 categories
   - Error handling: 8/9 (88.9%) -- only 404 nesting format differs
   - Ready for: `/pdca report news-intelligence-monitor`

11. **data-source-footer** (2026-02-19)
   - Match Rate: 98.8% (PASS)
   - Design doc: `docs/02-design/features/data-source-footer.design.md`
   - Analysis: `docs/03-analysis/data-source-footer.analysis.md`
   - 246 items checked: 239 matched, 1 partial, 6 missing (cosmetic CSS class)
   - Cross-cutting feature: 1 backend API extension + 6 dashboard pages (5 React + 1 Vanilla JS)
   - Backend: collector/status API extended with table_counts (15 tables) + 3 new collector keys
   - Frontend: DataSourceFooter React.memo component replicated across 5 pages; renderDSFooter() Vanilla JS in idea_board
   - Key gaps: .ds-badge-demo CSS missing (Low, no current usage), 5s fetch timeout absent (Low), .ds-footer padding omitted (Negligible)
   - 2 positive additions: extra table_counts tables for news_intelligence
   - Cross-consistency verified: All 6 pages resolve to same API URL, all 15 db_table refs match backend, all 22 DATA_SOURCES items match design
   - Ready for: `/pdca report data-source-footer`

12. **pdca-status-sync** (2026-02-19)
   - Match Rate: 97.2% (PASS)
   - Design doc: `docs/02-design/features/pdca-status-sync.design.md`
   - Analysis: `docs/03-analysis/features/pdca-status-sync.analysis.md`
   - 69 items checked: 65 matched, 1 partial, 2 changed (Negligible), 1 missing (Low)
   - Hybrid merge: Static REQ (project_status_data.js) + Dynamic PDCA (API) in both index.html and project_status.html
   - 5 files: config/pdca_id_map.json, backend/app/api/project_status.py, backend/app/main.py, dashboard/index.html, dashboard/project_status.html
   - Key: ID namespace separation (PDCA- vs REQ-) with pdca_id_map.json for immutable ID assignment
   - Noise filtering: 30 features in .pdca-status.json but only 5 have planPath (correctly filtered)
   - Error handling: 7/7 (100%) -- graceful degradation in both frontend pages
   - Missing: 2 CSS classes (.project-badge.badge-pdca, .badge-design in index.html) -- Low impact, source badges serve same purpose
   - 3 positive additions: _REQ_ITEMS module-level extraction, URL filter params, checklist counting
   - Ready for: `/pdca report pdca-status-sync`

13. **disclosure-auto-collect** (2026-02-19, RE-RUN v2.0)
   - Match Rate: 97.9% (PASS) -- was 75.0% in v1.0
   - Design doc: `docs/02-design/features/disclosure-auto-collect.design.md`
   - Analysis: `docs/03-analysis/features/disclosure-auto-collect.analysis.md`
   - 12 items checked: 11 matched, 1 changed (Low), 0 missing
   - 3 files: collector.py (backend), monitor_disclosures.html (frontend), run_daily_collect.bat (batch)
   - v1->v2 fixes: Design updated to async+polling pattern, toast partial distinction added, timer aligned to 8s
   - All 6 previously-PARTIAL items resolved by design update + UI fix
   - Remaining: run_all uses `_bg()` variant (intentional optimization, Low impact)
   - 8 positive additions: step labels, elapsed timer, already_running guard, cache-bust reload, etc.
   - Cross-consistency: 7/7 (100%), Error handling: 4/4 (100%)
   - Ready for: `/pdca report disclosure-auto-collect`

### Key Patterns

- Design doc covers dashboard (React/API) but moat estimator is a sub-feature (data pipeline)
- Python scripts in `scripts/stock_moat/` and utils in `.agent/skills/stock-moat/utils/`
- DART API key hardcoded in 4+ files -- recurring security concern
- Excel I/O uses atomic operations with backup/restore -- good pattern
- GICS classification with confidence scores -- investment-standard approach

### Analysis Methodology Notes

See detailed notes in `methodology-notes.md`. Key principles:
- Weight functional requirements (30-40%) higher than convention compliance (5%)
- "Added features" beyond design are positive indicators, not gaps
- Error handling is often the weakest category -- track separately
- Encoding mismatches (EUC-KR vs UTF-8) are Medium impact for Korean web scraping
- Full-stack features: check 7 categories (endpoints, models, schemas, service logic, frontend, error handling, router registration)
- Cross-cutting features: verify each page independently, use matrix tables for 6+ page comparisons
- Dashboard integration evolves: card-based monitoring sections replace header-actions buttons
- KIND enrichment: check BOTH backend data production AND frontend rendering of enriched fields
- Sync-to-async refactoring: When impl changes sync design to async (background thread + polling), count each affected layer as PARTIAL, not MISSING. Root cause is single architectural decision, not multiple independent gaps.
- Long-running scraping endpoints: async pattern with progress polling is architecturally superior; recommend design update rather than implementation revert
