import React from 'react';
import { Loader } from 'lucide-react';

const LoadingCard = () => {
  return (
    <div className="loading-spinner">
      <Loader size={40} className="spinner-icon" />
    </div>
  );
};

export default LoadingCard;
