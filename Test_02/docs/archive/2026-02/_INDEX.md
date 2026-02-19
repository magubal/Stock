# Archive Index - 2026-02

## Archived Features

### data-source-footer
- **Archived**: 2026-02-19
- **Match Rate**: 98.8%
- **Iterations**: 0
- **Duration**: 1 session (2026-02-19)
- **Documents**:
  - `data-source-footer/data-source-footer.plan.md`
  - `data-source-footer/data-source-footer.design.md`
  - `data-source-footer/data-source-footer.analysis.md`
  - `data-source-footer/data-source-footer.report.md`
- **Summary**: 6개 모니터링 대시보드 하단에 접이식 DataSourceFooter 추가. 하이브리드 방식(정적 JS 메타 + 동적 collector/status API). 22개 데이터 소스 매핑, 15개 DB 테이블 건수 조회. 5 React pages + 1 Vanilla JS page. ~820 lines added.

### news-intelligence-monitor
- **Archived**: 2026-02-19
- **Match Rate**: 98.4%
- **Iterations**: 0
- **Duration**: 1 day (2026-02-19)
- **Documents**:
  - `news-intelligence-monitor/news-intelligence-monitor.plan.md`
  - `news-intelligence-monitor/news-intelligence-monitor.design.md`
  - `news-intelligence-monitor/news-intelligence-monitor.analysis.md`
  - `news-intelligence-monitor/news-intelligence-monitor.report.md`
- **Summary**: Finviz 뉴스 5 카테고리 파싱 + Claude AI 분석 + Sector→Industry→Stock 3단계 drill-down. 5 DB models, 6 API endpoints, ~3,350 lines. Unified 4-step pipeline (News→Stock→Sector→AI) with coverage badge. v1.0→v1.2 in single day.

### evidence-based-moat
- **Archived**: 2026-02-09
- **Match Rate**: 95.2%
- **Iterations**: 1
- **Duration**: ~2 days (2026-02-09 ~ 2026-02-10)
- **Documents**:
  - `evidence-based-moat/evidence-based-moat.plan.md`
  - `evidence-based-moat/evidence-based-moat.design.md`
  - `evidence-based-moat/evidence-based-moat.analysis.md`
  - `evidence-based-moat/evidence-based-moat.report.md`
- **Summary**: DART 공시 데이터 기반 증거 중심 해자 평가 시스템 v2.0. 8 modules + pipeline orchestrator. Multi-agent collaboration (Claude + Gemini) with 4-file compatibility fix post-report.

### stock-moat-estimator
- **Archived**: 2026-02-09
- **Match Rate**: 98.4%
- **Iterations**: 0
- **Duration**: ~19 hours (2026-02-08 ~ 2026-02-09)
- **Documents**:
  - `stock-moat-estimator/stock-moat-estimator.plan.md`
  - `stock-moat-estimator/stock-moat-estimator.design.md`
  - `stock-moat-estimator/stock-moat-estimator.analysis.md`
  - `stock-moat-estimator/stock-moat-estimator.report.md`
- **Summary**: GICS 기반 해자 분석기 v1.0. 1561 Korean stocks (208 + 1353), 94.9% classification accuracy, 99.93% DART API success rate. Superseded by evidence-based-moat v2.0.
