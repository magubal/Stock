import useSWR from 'swr';
import { fetcher } from '../lib/fetcher';

export function usePsychology() {
  const { data, error, isLoading, mutate } = useSWR(
    '/api/v1/psychology',
    fetcher,
    {
      refreshInterval: 60000,       // Refresh every 60 seconds
      revalidateOnFocus: true,      // Revalidate when window gains focus
      dedupingInterval: 30000,      // Dedupe requests within 30 seconds
      errorRetryCount: 3,           // Retry 3 times on error
      shouldRetryOnError: true,
      revalidateOnReconnect: true
    }
  );

  return {
    psychology: data,
    isLoading,
    isError: error,
    refresh: mutate
  };
}
