# Gap Detector Methodology Notes

Detailed notes on analysis methodology patterns accumulated across 12+ analyses.

## Core Principles
- Weight functional requirements (30-40%) higher than convention compliance (5%)
- "Added features" beyond design are positive indicators, not gaps
- Data quality verification via reanalysis reports is critical for data pipeline features
- Security issues (hardcoded keys) reduce convention score but not match rate
- Stub methods (return None) count as PARTIAL, not MISSING -- interface exists

## Scoring Conventions
- print() vs logging is a convention gap but low impact for data pipeline scripts
- Test plan items without formal pytest files score 50% if __main__ blocks exist
- DI patterns (FastAPI Depends) and default fallback values count as positive additions
- response_model missing from FastAPI endpoints is Low severity but should be noted
- Error handling is often the weakest category -- track error_code, timestamp, HTTP status codes separately

## Full-Stack Feature Checks
- Full-stack features: check 7 categories (endpoints, models, schemas, service logic, frontend, error handling, router registration)
- Phase 3 (future) items should be excluded from match rate -- only count current phase scope
- Static-file pipeline features (scraper->analyzer->JSON->HTML): check pipeline paths, field schemas, and output data files as concrete evidence
- React CDN + Babel features: verify React.memo, useMemo, useCallback, null safety, stable keys for quality

## Korean Web Scraping
- Encoding mismatches (EUC-KR vs UTF-8) are Medium impact for Korean web scraping -- always flag
- apparent_encoding auto-detection is pragmatic but should be noted as CHANGED vs explicit EUC-KR

## Cross-Consistency Patterns
- Cross-consistency check: when models are duplicated across standalone scripts, verify all copies match canonical source
- Config-driven features (weights, ranges, symbols): verify config.py constants match design AND are used by all consumers
- Multi-file level/status mappings (backend LEVEL_MAP + frontend LEVEL_CONFIG + calculator score_to_level): verify all match
- News "Top N" designs: check if API supports N items or only returns single top -- frontend can only show what API provides

## External API Features
- When design specifies statistical thresholds (p80, p90) but no historical data store exists, fixed thresholds are acceptable MVP substitutes -- flag as CHANGED not MISSING
- Trigger engine verification: check threshold values, comparison operators, scoring logic (count->level mapping), and special cases

## UI/Frontend Patterns
- Gauge count mismatches: conditional gauges (render only when data available) are positive additions
- Modal/popup features not in design but enhancing UX should be counted as positive additions, not gaps
- Responsive breakpoint consistency: when implementation uses a different breakpoint than design but matches existing file conventions, classify as Negligible positive change

## MCP Features
- MCP tool parameter verification: check that tool parameters map to actual SQLAlchemy model fields -- wrong field names cause runtime TypeError
- MCP registration: .mcp.json is correct MCP standard, .claude/settings.json is older convention -- flag as CHANGED (Low, intentional)
- MCP tool bug verification on RE-RUN: always re-read the exact lines and verify SQLAlchemy model field names match tool keyword arguments

## Multi-Phase Features
- Multi-phase features (Phase 1/2/3): score each phase separately, exclude future-phase "Should" items from match rate
- Context Packet schema: design may specify comprehensive schema but implementation can use simplified version
- Extension/Intelligence Layer scope: when separately approved extensions exist beyond original design, analyze them as bonus items

## Dashboard Patterns
- Vanilla JS vs CDN React: when design says React CDN but implementation uses vanilla JS, count as CHANGED (Medium) not MISSING
- Dashboard rewrites: when implementation significantly exceeds design, score as CHANGED+EXCEEDED, not MISSING
- Vanilla JS equivalents of React components: verify same table structure, status logic, toggle behavior

## Design/Implementation Patterns
- When design and implementation are developed together (same session), expect near-100% match -- focus analysis on cross-consistency and error handling quality
- Signal->Idea conversion: verify both the service method AND the API endpoint that exposes it, plus MCP tool wrapper
- Multi-service features (3+ services): verify service independence (no circular deps) and that API layer properly orchestrates them

## Verification Criteria Patterns
- V-XX verification criteria: when design document defines numbered verification items (V-01..V-12), check each individually
- CSS removal verification: when design specifies classes to remove, grep for all of them to confirm zero matches
- data-testid compatibility: verify maintained/deleted/new testids against design table

## Cross-Cutting Feature Patterns
- Cross-cutting features (same component in N pages): verify each page independently
- API URL resolution: different pages may use different variable names but resolve to same endpoint
- CSS class omissions for unused features are Low impact but should be noted for future-proofing
- Hybrid merge features (static data + dynamic API): verify merge logic in BOTH frontend files
- ID namespace features (PDCA-XXX vs REQ-XXX): structurally different prefixes make collision impossible

## Disclosure-Monitoring Specific
- KIND detail page scraping: enrichment data (YoY%, contract amounts) is available in backend but frontend may not render it -- check both sides
- Cluster alert text: verify event_labels dict has Korean labels for all event classes, not just subset
- Dashboard integration style evolves: original design may say "green button in header" but implementation correctly uses card-based monitoring section
- HTTPException detail nesting: FastAPI wraps `detail` kwarg as `{"detail": <value>}` -- passing a dict causes double-nesting

## News Pipeline Patterns
- News pipeline features: verify 5 cross-consistency dimensions: model fields, config constants, category mappings, sentiment labels, DEMO markers
- Seed data article count: templates * days = total rows
- Multi-source extensible parsers: when design lists "future sources" slots, only check currently implemented sources
