import { useState, useEffect, useCallback } from "react";
import apiClient from "@/api/client";
import type { AxiosRequestConfig } from "axios";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiOptions extends AxiosRequestConfig {
  enabled?: boolean;
}

export function useApi<T>(url: string, options?: UseApiOptions) {
  const { enabled = true, ...config } = options ?? {};

  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: enabled,
    error: null,
  });

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    setState({ data: null, loading: true, error: null });
    try {
      const response = await apiClient.get<T>(url, config);
      setState({ data: response.data, loading: false, error: null });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred";
      setState({ data: null, loading: false, error: message });
    }
  }, [url, enabled]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
