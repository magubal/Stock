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

4. **disclosure-monitoring** (2026-02-14)
   - Match Rate: 96.4% (PASS)
   - Design doc: `docs/02-design/features/disclosure-monitoring.design.md`
   - Analysis: `docs/03-analysis/features/disclosure-monitoring.analysis.md`
   - 86 items checked: 81 matched, 3 changed, 1 missing, 10 added
   - Pipeline: KIND collector -> analyzer -> JSON -> React CDN frontend
   - Key gaps: EUC-KR vs UTF-8 encoding (Medium), dilution_total->dilution_count (Low), Excel fallback missing (Low)
   - Added: sample data generator, 5 extra taxonomy keywords, archive output, file logging
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

### Key Patterns

- Design doc covers dashboard (React/API) but moat estimator is a sub-feature (data pipeline)
- Python scripts in `scripts/stock_moat/` and utils in `.agent/skills/stock-moat/utils/`
- DART API key hardcoded in 4+ files -- recurring security concern
- Excel I/O uses atomic operations with backup/restore -- good pattern
- GICS classification with confidence scores -- investment-standard approach

### Analysis Methodology Notes

- Weight functional requirements (30%) higher than convention compliance (5%)
- "Added features" beyond design are positive indicators, not gaps
- Data quality verification via reanalysis reports is critical for data pipeline features
- Security issues (hardcoded keys) reduce convention score but not match rate
- Stub methods (return None) count as PARTIAL, not MISSING -- interface exists
- print() vs logging is a convention gap but low impact for data pipeline scripts
- Test plan items without formal pytest files score 50% if __main__ blocks exist
- Full-stack features: check 7 categories (endpoints, models, schemas, service logic, frontend, error handling, router registration)
- Phase 3 (future) items should be excluded from match rate -- only count current phase scope
- DI patterns (FastAPI Depends) and default fallback values count as positive additions
- response_model missing from FastAPI endpoints is Low severity but should be noted
- Error handling is often the weakest category -- track error_code, timestamp, HTTP status codes separately
- Static-file pipeline features (scraper->analyzer->JSON->HTML): check pipeline paths, field schemas, and output data files as concrete evidence
- React CDN + Babel features: verify React.memo, useMemo, useCallback, null safety, stable keys for quality
- Encoding mismatches (EUC-KR vs UTF-8) are Medium impact for Korean web scraping -- always flag
- Cross-consistency check: when models are duplicated across standalone scripts, verify all copies match canonical source
- Config-driven features (weights, ranges, symbols): verify config.py constants match design AND are used by all consumers
- Multi-file level/status mappings (backend LEVEL_MAP + frontend LEVEL_CONFIG + calculator score_to_level): verify all match
- News "Top N" designs: check if API supports N items or only returns single top -- frontend can only show what API provides
- External API features: when design specifies statistical thresholds (p80, p90) but no historical data store exists, fixed thresholds are acceptable MVP substitutes -- flag as CHANGED not MISSING
- Trigger engine verification: check threshold values, comparison operators, scoring logic (count->level mapping), and special cases (e.g., MVRV regime change = always HIGH)
- Gauge count mismatches: conditional gauges (render only when data available) are positive additions if the data source was already in the plan
- Modal/popup features not in design but enhancing UX should be counted as positive additions, not gaps
- MCP tool parameter verification: check that tool parameters map to actual SQLAlchemy model fields -- wrong field names cause runtime TypeError
- Multi-phase features (Phase 1/2/3): score each phase separately, exclude future-phase "Should" items from match rate
- Context Packet schema: design may specify comprehensive schema but implementation can use simplified version -- check PROTOCOL.md for alignment
- Vanilla JS vs CDN React: when design says React CDN but implementation uses vanilla JS, count as CHANGED (Medium) not MISSING -- functionally equivalent
- MCP registration: .mcp.json is correct MCP standard, .claude/settings.json is older convention -- flag as CHANGED (Low, intentional)
- Extension/Intelligence Layer scope: when separately approved extensions exist beyond original design, analyze them as bonus items (100% bonus score) but include in overall count
- Cross-module aggregation services: verify each data source (DB queries, file reads, cache reads) individually -- 7+ modules need per-module verification
- Custom data source plugins (auto-load *.json from directory): verify both the example file AND the service auto-load logic
- Dashboard rewrites: when implementation significantly exceeds design (e.g., Kanban -> Intelligence Dashboard), score as CHANGED+EXCEEDED, not MISSING
- MCP tool bug verification on RE-RUN: always re-read the exact lines and verify SQLAlchemy model field names match tool keyword arguments
- Rule engine features: verify rules JSON -> engine extractor -> condition evaluator -> signal creator full chain, plus dashboard color/label mapping
- When design and implementation are developed together (same session), expect near-100% match -- focus analysis on cross-consistency and error handling quality
- Signal->Idea conversion: verify both the service method AND the API endpoint that exposes it, plus MCP tool wrapper
- Multi-service features (3+ services): verify service independence (no circular deps) and that API layer properly orchestrates them
