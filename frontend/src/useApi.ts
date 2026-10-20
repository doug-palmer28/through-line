import { useEffect, useState } from "react";

// Loads data once on mount. Returns the data, any error, and a loading flag.
export function useApi<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    load()
      .then((d) => active && setData(d))
      .catch((e: Error) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [load]);

  return { data, error, loading: data === null && error === null };
}
