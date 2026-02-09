import React from 'react';
import { AlertTriangle } from 'lucide-react';

const ErrorFallback = ({ error, onRetry }) => {
  return (
    <div className="error-fallback">
      <AlertTriangle size={24} className="error-icon" />
      <p className="error-message">데이터를 불러올 수 없습니다</p>
      {error && (
        <p className="error-detail">{error.message || '알 수 없는 오류가 발생했습니다'}</p>
      )}
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  );
};

export default ErrorFallback;
