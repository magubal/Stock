import useSWR from 'swr';
import { fetcher } from '../lib/fetcher';

export function useFlywheel() {
  const { data, error, isLoading, mutate } = useSWR(
    '/api/v1/flywheel',
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
    flywheel: data,
    isLoading,
    isError: error,
    refresh: mutate
  };
}
