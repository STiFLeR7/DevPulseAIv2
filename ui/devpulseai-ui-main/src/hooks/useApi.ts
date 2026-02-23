import { useState, useEffect, useCallback } from 'react';

interface UseApiResult<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

/**
 * Generic data-fetching hook.
 * Calls `fetcher` on mount and whenever `deps` change.
 */
export function useApi<T>(
    fetcher: () => Promise<T>,
    deps: unknown[] = [],
): UseApiResult<T> {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await fetcher();
            setData(result);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Unknown error';
            setError(msg);
            console.error('[useApi]', msg);
        } finally {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, deps);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}
