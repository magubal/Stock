import React from 'react';
import { Brain, Clock, Briefcase, Building, GitBranch, RefreshCw, TrendingUp, Check, Circle, Loader, AlertTriangle, Activity, Users, Newspaper, ArrowRight } from 'lucide-react';
import './Dashboard.css';
import { usePsychology } from '../../hooks/usePsychology';
import { useTiming } from '../../hooks/useTiming';
import { usePortfolio } from '../../hooks/usePortfolio';
import { useEvaluation } from '../../hooks/useEvaluation';
import { useContextAnalysis } from '../../hooks/useContextAnalysis';
import { useFlywheel } from '../../hooks/useFlywheel';
import DashboardCard from '../shared/DashboardCard';

// 투자자 심리 분석 컴포넌트
const PsychologyMetrics = React.memo(({ data }) => {
  const investorTypes = data?.investorTypes || [];
  return (
    <div className="psychology-metrics">
      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">시장 과열도</span>
          <div className="metric-progress">
            <div className="progress-bar" style={{ '--progress-width': `${data?.marketHeat || 0}%` }}></div>
          </div>
          <span className="metric-value">{data?.marketHeat || 0}%</span>
        </div>

        <div className="metric-item">
          <span className="metric-label">투자자 공감도</span>
          <div className="metric-progress">
            <div className="progress-bar positive" style={{ '--progress-width': `${data?.empathy || 0}%` }}></div>
          </div>
          <span className="metric-value positive">{data?.empathy || 0}%</span>
        </div>

        <div className="metric-item">
          <span className="metric-label">기대감 레벨</span>
          <div className="metric-progress">
            <div className="progress-bar" style={{ '--progress-width': `${data?.expectation || 0}%` }}></div>
          </div>
          <span className="metric-value">{data?.expectation || 0}%</span>
        </div>
      </div>

      <div className="investor-types">
        <h4>투자자 유형별 심리</h4>
        {investorTypes.map((type) => (
          <div key={type.type} className="investor-type">
            <span className="type-label">{type.type}</span>
            <span className={`type-indicator indicator-${type.sentiment}`}>
              {type.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
});

// 투자 타이밍 분석 컴포넌트
const TimingAnalysis = React.memo(({ data }) => {
  if (!Array.isArray(data)) return <div className="timeline-analysis">데이터 없음</div>;
  return (
    <div className="timeline-analysis">
      {data.map((item) => (
        <div key={item.period} className="timeline-item">
          <div className="timeline-period">{item.period}</div>
          <div className={`timeline-signal signal-${item.signal}`}>
            {item.signal === 'good' ? <TrendingUp size={16} /> : <AlertTriangle size={16} />}
            <span>{item.label}</span>
          </div>
          <div className="timeline-reason">{item.reason}</div>
        </div>
      ))}
    </div>
  );
});

// 포트폴리오 개요 컴포넌트
const PortfolioOverview = React.memo(({ data }) => {
  const alerts = data?.alerts || [];
  return (
    <div className="portfolio-overview">
      <div className="portfolio-stats">
        <div className="stat-item">
          <span className="stat-label">보유 종목</span>
          <span className="stat-value">{data.totalStocks}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">평균 수익률</span>
          <span className="stat-value positive">+{data.avgReturn}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">매도 신호</span>
          <span className="stat-value warning">{data.sellSignals}</span>
        </div>
      </div>

      <div className="portfolio-alerts">
        {alerts.map((alert) => (
          <div key={alert.type} className={`alert-item alert-${alert.type}`}>
            {alert.type === 'price-burden' ? (
              <AlertTriangle size={20} className="alert-icon" />
            ) : (
              <Activity size={20} className="alert-icon" />
            )}
            <div className="alert-content">
              <div className="alert-title">{alert.title}</div>
              <div className="alert-description">{alert.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

// 기업 평가 컴포넌트
const CompanyEvaluation = React.memo(({ data }) => {
  const valueProposition = data?.valueProposition || [];
  const industryEvaluation = data?.industryEvaluation || [];
  return (
    <div className="company-evaluation">
      <div className="eval-section">
        <h4>고객가치제안 평가</h4>
        <div className="checklist">
          {valueProposition.map((item) => (
            <div key={item.label} className={`checklist-item ${item.checked ? 'checked' : 'pending'}`}>
              {item.checked ? <Check size={16} /> : <Circle size={16} />}
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="eval-section">
        <h4>산업 평가</h4>
        <div className="industry-scores">
          {industryEvaluation.map((item) => (
            <div key={item.name} className="score-item">
              <span className="score-label">{item.name}</span>
              <span className={`score score-${item.color}`}>{item.score}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

// 맥락 연결 분석기 컴포넌트
const ContextAnalyzer = React.memo(({ data }) => {
  // API 응답을 컴포넌트 형태로 변환
  const apiData = data?.data || data || {};
  const sentiment = apiData.overall_sentiment || 'neutral';
  const sentimentLabel = { positive: '긍정', negative: '부정', neutral: '중립' }[sentiment] || sentiment;
  const sentimentColor = { positive: 'positive', negative: 'danger', neutral: '' }[sentiment] || '';

  const flow = [
    { Icon: Newspaper, label: '뉴스 수집' },
    { Icon: Brain, label: '감성 분석' },
    { Icon: Activity, label: '시장 영향' },
    { Icon: Users, label: '투자자 행동' },
  ];

  const insights = [
    { label: '전체 감성', value: sentimentLabel, color: sentimentColor },
    { label: '시장 방향', value: apiData.market_direction || '보합' },
    { label: '분석 건수', value: `${apiData.analysis_count || 0}건` },
  ];

  return (
    <div className="context-analyzer">
      <div className="context-flow">
        {flow.map((item, index) => (
          <React.Fragment key={item.label}>
            <div className="flow-node">
              <item.Icon size={24} />
              <span>{item.label}</span>
            </div>
            {index < flow.length - 1 && <ArrowRight size={20} className="flow-arrow" />}
          </React.Fragment>
        ))}
      </div>

      <div className="context-insights">
        {insights.map((insight) => (
          <div key={insight.label} className="insight-item">
            <span className="insight-label">{insight.label}</span>
            <span className={`insight-value ${insight.color || ''}`}>{insight.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
});

// 플라이휘 상태 컴포넌트
const FlywheelStatus = React.memo(({ data }) => {
  const progress = data?.progress || [];
  return (
    <div className="flywheel-status">
      <div className="cycle-progress">
        <div className="progress-circle">
          <span className="progress-text">{data?.currentStep || 1}/{data?.totalSteps || 7}</span>
        </div>
        <span className="progress-label">{data?.currentPhase || '-'}</span>
      </div>

      <div className="cycle-results">
        {progress.map((item) => (
          <div key={item.step} className={`result-item ${item.status}`}>
            {item.status === 'completed' && <Check size={16} />}
            {item.status === 'current' && <Loader size={16} />}
            {item.status === 'pending' && <Circle size={16} />}
            <span>{item.step}</span>
          </div>
        ))}
      </div>
    </div>
  );
});

const Dashboard = () => {
  // Fetch data from API using SWR hooks
  const { psychology, isLoading: psychLoading, isError: psychError, refresh: refreshPsych } = usePsychology();
  const { timing, isLoading: timingLoading, isError: timingError, refresh: refreshTiming } = useTiming();
  const { portfolio, isLoading: portfolioLoading, isError: portfolioError, refresh: refreshPortfolio } = usePortfolio();
  const { evaluation, isLoading: evalLoading, isError: evalError, refresh: refreshEval } = useEvaluation();
  const { context, isLoading: contextLoading, isError: contextError, refresh: refreshContext } = useContextAnalysis();
  const { flywheel, isLoading: flywheelLoading, isError: flywheelError, refresh: refreshFlywheel } = useFlywheel();

  // Refresh all data
  const handleRefreshAll = () => {
    refreshPsych();
    refreshTiming();
    refreshPortfolio();
    refreshEval();
    refreshContext();
    refreshFlywheel();
  };

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">
              <TrendingUp size={24} />
            </div>
            <span>Stock Research <span className="highlight">ONE</span></span>
          </div>
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={handleRefreshAll}>
              새로고침
            </button>
            <button className="btn btn-primary">데이터 수집</button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="dashboard-grid">
          {/* 투자자 심리 분석 */}
          <DashboardCard
            className="featured"
            loading={psychLoading}
            error={psychError}
            onRetry={refreshPsych}
          >
            <div className="card-header">
              <div className="card-icon">
                <Brain size={20} />
              </div>
              <h3 className="card-title">투자자 심리 분석</h3>
            </div>
            <div className="card-content">
              {psychology && <PsychologyMetrics data={psychology} />}
            </div>
          </DashboardCard>

          {/* 투자 타이밍 분석 */}
          <DashboardCard loading={timingLoading} error={timingError} onRetry={refreshTiming}>
            <div className="card-header">
              <div className="card-icon">
                <Clock size={20} />
              </div>
              <h3 className="card-title">투자 타이밍 분석</h3>
            </div>
            <div className="card-content">
              {timing && <TimingAnalysis data={timing} />}
            </div>
          </DashboardCard>

          {/* 포트폴리오 관리 */}
          <DashboardCard loading={portfolioLoading} error={portfolioError} onRetry={refreshPortfolio}>
            <div className="card-header">
              <div className="card-icon">
                <Briefcase size={20} />
              </div>
              <h3 className="card-title">중장기 포트폴리오</h3>
            </div>
            <div className="card-content">
              {portfolio && <PortfolioOverview data={portfolio} />}
            </div>
          </DashboardCard>

          {/* 기업 평가 워크스페이스 */}
          <DashboardCard loading={evalLoading} error={evalError} onRetry={refreshEval}>
            <div className="card-header">
              <div className="card-icon">
                <Building size={20} />
              </div>
              <h3 className="card-title">기업 평가 워크스페이스</h3>
            </div>
            <div className="card-content">
              {evaluation && <CompanyEvaluation data={evaluation} />}
            </div>
          </DashboardCard>

          {/* 맥락 연결 분석기 */}
          <DashboardCard loading={contextLoading} error={contextError} onRetry={refreshContext}>
            <div className="card-header">
              <div className="card-icon">
                <GitBranch size={20} />
              </div>
              <h3 className="card-title">맥락 연결 분석기</h3>
            </div>
            <div className="card-content">
              {context && <ContextAnalyzer data={context} />}
            </div>
          </DashboardCard>

          {/* 플라이휘 실행 현황 */}
          <DashboardCard loading={flywheelLoading} error={flywheelError} onRetry={refreshFlywheel}>
            <div className="card-header">
              <div className="card-icon">
                <RefreshCw size={20} />
              </div>
              <h3 className="card-title">플라이휘 실행 현황</h3>
            </div>
            <div className="card-content">
              {flywheel && <FlywheelStatus data={flywheel} />}
            </div>
          </DashboardCard>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;