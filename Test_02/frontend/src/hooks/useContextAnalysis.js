import useSWR from 'swr';
import { fetcher } from '../lib/fetcher';

export function useContextAnalysis() {
  const { data, error, isLoading, mutate } = useSWR(
    '/context-analysis/market-sentiment-summary?hours=24',
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
    context: data,
    isLoading,
    isError: error,
    refresh: mutate
  };
}
