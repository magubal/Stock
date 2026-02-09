import React from 'react';
import LoadingCard from './LoadingCard';
import ErrorFallback from './ErrorFallback';

const DashboardCard = ({
  loading,
  error,
  onRetry,
  children,
  className = '',
  ...props
}) => {
  if (loading) {
    return (
      <div className={`dashboard-card ${className}`} {...props}>
        <LoadingCard />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`dashboard-card ${className}`} {...props}>
        <ErrorFallback error={error} onRetry={onRetry} />
      </div>
    );
  }

  return (
    <div className={`dashboard-card ${className}`} {...props}>
      {children}
    </div>
  );
};

export default DashboardCard;
