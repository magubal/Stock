import useSWR from 'swr';
import { fetcher } from '../lib/fetcher';

export function usePortfolio() {
  const { data, error, isLoading, mutate } = useSWR(
    '/api/v1/portfolio',
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
    portfolio: data,
    isLoading,
    isError: error,
    refresh: mutate
  };
}
