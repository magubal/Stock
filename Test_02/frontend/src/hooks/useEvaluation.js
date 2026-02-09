import useSWR from 'swr';
import { fetcher } from '../lib/fetcher';

export function useEvaluation(stockCode = null) {
  const url = stockCode
    ? `/api/v1/evaluation?stock_code=${stockCode}`
    : '/api/v1/evaluation';

  const { data, error, isLoading, mutate } = useSWR(
    url,
    fetcher,
    {
      refreshInterval: 60000,
      revalidateOnFocus: true,
      dedupingInterval: 30000,
      errorRetryCount: 3,
      shouldRetryOnError: true,
      revalidateOnReconnect: true
    }
  );

  return {
    evaluation: data,
    isLoading,
    isError: error,
    refresh: mutate
  };
}
