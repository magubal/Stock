# bkit-report-generator Agent Memory

## Project Context
- **Project**: Stock Research ONE (한국어 주식 리서치 자동화)
- **Feature Reporting**: PDCA completion reports for agent-driven features
- **Report Location**: `docs/04-report/features/`

## Key Patterns

### Report Generation Workflow
1. Read Plan (`01-plan/features/{feature}.plan.md`) — requirements & FRs
2. Read Design (`02-design/features/{feature}.design.md`) — architecture & specifications
3. Read Analysis (`03-analysis/features/{feature}.analysis.md`) — gap analysis & match rates
4. Generate Report (`04-report/features/{feature}.report.md`) — integrated summary

### Report Structure (Standard Template)
- Executive Summary with PDCA cycle status
- Related Documents (cross-references)
- Completed Requirements (FR matrix)
- Quality Metrics (match rates, scores)
- Lessons Learned (retrospective in Keep/Problem/Try format)
- File Manifest (all deliverables)
- Changelog (v1.0, v2.0 format)
- Success Criteria verification
- Next steps & recommendations

### Match Rate Interpretation
- **96%+**: PASS, production-ready (idea-ai-collaboration: 96.2%)
- **90-95%**: PASS, minor issues documented
- **<90%**: Flag for improvement cycle (usually triggers /pdca iterate)
- Phase 3 "Should" items typically excluded from score if deferred

### Phase Classification
- **Phase 1**: Core MVP features (Must priority)
- **Phase 2**: Enhanced capabilities + integration (Should/Must)
- **Phase 2 IL**: Intelligence Layer (bonus implementation beyond design)
- **Phase 3**: Advanced features (Usually Should priority, often deferred)

## Project-Specific Insights

### Stock Research ONE Structure
- Three dashboard systems exist:
  - `frontend/` (Vite React SPA — localhost:3000)
  - `dashboard/` (Static HTML + CDN React — for backend integration)
  - Backend API (`/api/v1/*` routers) — FastAPI (localhost:8000)
- All new dashboards should use static HTML + CDN React pattern (not React SPA)

### PDCA Status Tracking
- Global status: `.pdca-status.json` tracks feature phases
- Features can have multiple iterations (v1.0, v2.0, etc.)
- Critical bugs discovered in v1.0 should trigger v2.0 RE-RUN
- Phase 2 Intelligence Layer commonly exceeds original design scope

### Database Models Convention
- 6 tables = standard feature (daily_work, insights, evidence, packets, sessions, etc.)
- All models get registered in `backend/app/models/__init__.py`
- SQLite TEXT for JSON arrays (not native JSON support)
- Always use timezone-aware DateTime fields

### API Endpoint Naming
- Resource-based: `/api/v1/{resource}` (daily-work, insights, ideas, collab, cross-module)
- CRUD: POST (create), GET (list), GET/{id} (single), PUT/{id} (update), DELETE/{id} (delete)
- Advanced: POST/extract, GET/stats, GET/{id}/evidence (domain-specific actions)

### MCP Server Integration
- Claude uses MCP (Model Context Protocol) via `.mcp.json` registration
- 8 tools (queries + actions) + 4 resources (documents + state) is typical scope
- All tools need try/finally for proper resource cleanup
- Tools use absolute file paths (Windows/Linux compatibility critical)

### Parser Pipeline Pattern
- BaseParser abstract class → enables extensibility
- Each format needs: supports() method + parse() method
- DailyWorkRow dataclass for standardized output
- Content dedup via SHA-256 hash (prevents duplicate entries)

## Known Challenges

### Context Packet Schema Evolution
- Design often specifies comprehensive nested structure
- Implementation uses simplified flat structure for MCP tool ergonomics
- This is acceptable if COLLAB_PROTOCOL.md documents the simplified format
- External imports can accept full format via import_packet flexibility

### Phase 3 Scope Management
- "Should" priority items are easy to defer without explicit resource allocation
- Recommendation: Add Phase 3 items to next cycle immediately after Phase 2 completion
- Document deferral reason explicitly (time constraint, lower priority, etc.)

### Dashboard Pattern Consistency
- Static HTML dashboards should follow same pattern (CDN React, not vanilla JS)
- Inconsistency: idea_board.html vanilla JS vs liquidity_stress.html CDN React
- Lesson: Establish technical pattern standards before design approval

### MCP Registration Standards
- `.claude/settings.json` was legacy, `.mcp.json` is current standard
- Use absolute file paths for reliability on Windows
- Always set DATABASE_URL env var in MCP config

## Successful Techniques

### Effective Gap Analysis
- Re-run analysis (v2.0) after critical bug fixes to verify completeness
- Phase 2 IL extension often reveals design gaps (e.g., CrossModuleService use case)
- Document "changed but equivalent" items to explain design vs implementation divergence

### Comprehensive Retrospective
- Keep/Problem/Try format works well for team learning
- Connect lessons to concrete project artifacts (Design Section X, File Y)
- Include "Try Next Time" suggestions tied to specific improvements

### Extensibility Validation
- Confirm that BaseParser enables new format addition with minimal code
- Check that service layer can be extended without API layer changes
- Verify plugin pattern works (custom_sources auto-load example)

---

## Current Feature Status

### idea-ai-collaboration (Completed 2026-02-14)
- Report: `docs/04-report/features/idea-ai-collaboration.report.md` (1,500+ lines)
- Match Rate: 96.2% (v2.0 after bug fix)
- Critical Bug: MCP `create_idea_from_insights` FIXED (description→content field)
- Phase 2 IL: 8 bonus items fully implemented
- Files Delivered: 36 (31 code + 5 documentation)
- MCP Tools: 8 (all verified functional)
- API Endpoints: 26 (23 design + 3 bonus)

**Next Cycle**: Phase 3 (idea_connections, idea_outcomes) + external AI integration testing

---

## Report Quality Checklist

Before finalizing a completion report, verify:
- [ ] Plan/Design/Analysis documents cross-referenced correctly
- [ ] Match rates clearly explained (design match, architecture, convention)
- [ ] All Must FRs marked as complete (100%)
- [ ] Should FRs explicitly deferred or completed (with reason)
- [ ] File manifest lists all deliverables with line counts
- [ ] Critical bugs/fixes documented prominently
- [ ] Phase 2 IL bonus items acknowledged
- [ ] Lessons learned connected to concrete project examples
- [ ] Next cycle recommendations specific and actionable
- [ ] Changelog follows v1.0/v2.0 format
- [ ] Deployment checklist confirms production readiness

---

## Reference Templates

### Match Rate Scoring
```
Must FRs (80% weight):  20/20 = 100% * 0.8 = 80 pts
Should FRs (20% weight): 2.5/4 = 62.5% * 0.2 = 12.5 pts
Weighted Score: 80 + 12.5 = 92.5%
Design Detail (item-level): (175 + 8.25) / 186 = 98.5%
Severity-adjusted: 98.4% (after deductions)
Final (Phase 2 IL bonus): 96.2%
```

### Critical Bug Documentation
```
**v1.0 Bug**: [Description]
**Severity**: Critical/High/Medium/Low
**Fix**: [Implementation detail with line reference]
**Verification**: [How it was confirmed fixed]
**Status**: RESOLVED ✅
```

### Phase Delineation
```
**Phase 1**: [N items] — Core features (MVP)
**Phase 2**: [N items] — Integration features
**Phase 2 IL**: [N items] — Intelligence Layer extension (bonus)
**Phase 3**: [N items] — Advanced features (Should priority, deferred)
```
