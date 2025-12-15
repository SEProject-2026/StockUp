import { API_BASE_URL } from "@/src/config/api";
import { getAccessToken } from "@/src/auth/token";

export type ApiErrorShape = { detail?: string; message?: string; status?: string; [k: string]: any };

async function parseError(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const json = JSON.parse(text) as ApiErrorShape;
    return json.detail ?? json.message ?? `HTTP ${res.status}`;
  } catch {
    return text || `HTTP ${res.status}`;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) throw new Error(await parseError(res));

  return (await res.json()) as T;
}

export async function authFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAccessToken();
  return apiFetch<T>(path, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
}
