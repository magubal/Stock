import React from 'react';
import { Brain, Clock, Briefcase, Building, GitBranch, RefreshCw, TrendingUp, Check, Circle, Loader, AlertTriangle, Activity, Users, Newspaper, ArrowRight } from 'lucide-react';
import './Dashboard.css';

// 투자자 심리 분석 컴포넌트
const PsychologyMetrics = React.memo(({ data }) => {
  return (
    <div className="psychology-metrics">
      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">시장 과열도</span>
          <div className="metric-progress">
            <div className="progress-bar" style={{ '--progress-width': `${data.marketHeat}%` }}></div>
          </div>
          <span className="metric-value">{data.marketHeat}%</span>
        </div>

        <div className="metric-item">
          <span className="metric-label">투자자 공감도</span>
          <div className="metric-progress">
            <div className="progress-bar positive" style={{ '--progress-width': `${data.empathy}%` }}></div>
          </div>
          <span className="metric-value positive">{data.empathy}%</span>
        </div>

        <div className="metric-item">
          <span className="metric-label">기대감 레벨</span>
          <div className="metric-progress">
            <div className="progress-bar" style={{ '--progress-width': `${data.expectation}%` }}></div>
          </div>
          <span className="metric-value">{data.expectation}%</span>
        </div>
      </div>

      <div className="investor-types">
        <h4>투자자 유형별 심리</h4>
        {data.investorTypes.map((type) => (
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
        {data.alerts.map((alert) => (
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
  return (
    <div className="company-evaluation">
      <div className="eval-section">
        <h4>고객가치제안 평가</h4>
        <div className="checklist">
          {data.valueProposition.map((item) => (
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
          {data.industryEvaluation.map((item) => (
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
  return (
    <div className="context-analyzer">
      <div className="context-flow">
        {data.flow.map((item, index) => (
          <React.Fragment key={item.label}>
            <div className="flow-node">
              <item.icon size={24} />
              <span>{item.label}</span>
            </div>
            {index < data.flow.length - 1 && <ArrowRight size={20} className="flow-arrow" />}
          </React.Fragment>
        ))}
      </div>

      <div className="context-insights">
        {data.insights.map((insight) => (
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
  return (
    <div className="flywheel-status">
      <div className="cycle-progress">
        <div className="progress-circle">
          <span className="progress-text">{data.currentStep}/{data.totalSteps}</span>
        </div>
        <span className="progress-label">{data.currentPhase}</span>
      </div>

      <div className="cycle-results">
        {data.progress.map((item) => (
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
  // Mock data - 실제로는 API에서 가져옴
  const dashboardData = {
    psychology: {
      marketHeat: 35,
      empathy: 72,
      expectation: 58,
      investorTypes: [
        { type: '단기 투자자', sentiment: 'cautious', label: '보수적' },
        { type: '중장기 투자자', sentiment: 'optimistic', label: '긍정적' },
        { type: '보유자', sentiment: 'neutral', label: '중립적' },
        { type: '잠재 투자자', sentiment: 'interested', label: '관심 높음' }
      ]
    },
    timing: [
      { period: '3개월', signal: 'good', label: '투자 적합', reason: '기대요소 > 우려요소' },
      { period: '6개월', signal: 'good', label: '투자 적합', reason: '구조적 성장 기대' },
      { period: '1년', signal: 'caution', label: '주의 필요', reason: '변동성 증가 예상' }
    ],
    portfolio: {
      totalStocks: 12,
      avgReturn: 24.8,
      sellSignals: 3,
      alerts: [
        { type: 'price-burden', title: '가격부담 신호', description: '2개 종목에서 감지됨' },
        { type: 'volatility', title: '변동성 증가', description: '시장 전반적 영향' }
      ]
    },
    companyEvaluation: {
      valueProposition: [
        { checked: true, label: '차별적 혜택 철학 보유' },
        { checked: true, label: '실질적 실행 증거 확인' },
        { checked: false, label: '경쟁력 상승 지속성' }
      ],
      industryEvaluation: [
        { name: '빅트렌드 부합도', score: 85, color: 'positive' },
        { name: '해자 요인', score: 70, color: 'warning' },
        { name: '성장 변수', score: 60, color: 'warning' }
      ]
    },
    contextAnalysis: {
      flow: [
        { icon: Newspaper, label: '뉴스/이슈' },
        { icon: Brain, label: '투자심리' },
        { icon: Users, label: '행동 예측' }
      ],
      insights: [
        { label: '최신 이슈', value: 'Fed 금리 동결' },
        { label: '심리 영향', value: '긍정적 (+68%)', color: 'positive' },
        { label: '행동 가능성', value: '매수 유도 (확률 72%)', color: 'positive' }
      ]
    },
    flywheel: {
      currentStep: 4,
      totalSteps: 7,
      currentPhase: '시나리오 작성 단계',
      progress: [
        { step: '데이터 수집', status: 'completed' },
        { step: '맥락 분석', status: 'completed' },
        { step: '중요도 평가', status: 'completed' },
        { step: '시나리오 작성', status: 'current' },
        { step: '실질 확인', status: 'pending' }
      ]
    }
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
            <button className="btn btn-secondary">새로고침</button>
            <button className="btn btn-primary">데이터 수집</button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="dashboard-grid">
          {/* 투자자 심리 분석 */}
          <div className="dashboard-card featured">
            <div className="card-header">
              <div className="card-icon">
                <Brain size={20} />
              </div>
              <h3 className="card-title">투자자 심리 분석</h3>
            </div>
            <div className="card-content">
              <PsychologyMetrics data={dashboardData.psychology} />
            </div>
          </div>

          {/* 투자 타이밍 분석 */}
          <div className="dashboard-card">
            <div className="card-header">
              <div className="card-icon">
                <Clock size={20} />
              </div>
              <h3 className="card-title">투자 타이밍 분석</h3>
            </div>
            <div className="card-content">
              <TimingAnalysis data={dashboardData.timing} />
            </div>
          </div>

          {/* 포트폴리오 관리 */}
          <div className="dashboard-card">
            <div className="card-header">
              <div className="card-icon">
                <Briefcase size={20} />
              </div>
              <h3 className="card-title">중장기 포트폴리오</h3>
            </div>
            <div className="card-content">
              <PortfolioOverview data={dashboardData.portfolio} />
            </div>
          </div>

          {/* 기업 평가 워크스페이스 */}
          <div className="dashboard-card">
            <div className="card-header">
              <div className="card-icon">
                <Building size={20} />
              </div>
              <h3 className="card-title">기업 평가 워크스페이스</h3>
            </div>
            <div className="card-content">
              <CompanyEvaluation data={dashboardData.companyEvaluation} />
            </div>
          </div>

          {/* 맥락 연결 분석기 */}
          <div className="dashboard-card">
            <div className="card-header">
              <div className="card-icon">
                <GitBranch size={20} />
              </div>
              <h3 className="card-title">맥락 연결 분석기</h3>
            </div>
            <div className="card-content">
              <ContextAnalyzer data={dashboardData.contextAnalysis} />
            </div>
          </div>

          {/* 플라이휘 실행 현황 */}
          <div className="dashboard-card">
            <div className="card-header">
              <div className="card-icon">
                <RefreshCw size={20} />
              </div>
              <h3 className="card-title">플라이휘 실행 현황</h3>
            </div>
            <div className="card-content">
              <FlywheelStatus data={dashboardData.flywheel} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;