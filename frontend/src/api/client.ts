import { API_BASE_URL } from "@/src/config/api";
import { getSelectedHomeId } from "../utils/selected-home";
import { supabase } from "../config/supabase";

type FastApiDetailItem = {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
  [k: string]: any;
};

export type ApiErrorShape = {
  detail?: string | FastApiDetailItem[];
  message?: string;
  status?: string;
  [k: string]: any;
};

function formatFastApiDetail(detail: ApiErrorShape["detail"], fallback: string) {
  if (!detail) return fallback;

  // detail as string
  if (typeof detail === "string") return detail;

  // detail as list of validation errors
  if (Array.isArray(detail)) {
    const lines = detail.map((e) => {
      const loc = Array.isArray(e.loc) ? e.loc.join(".") : "body";
      const msg = e.msg ?? "Validation error";
      return `${loc}: ${msg}`;
    });
    return lines.join("\n");
  }

  return fallback;
}

async function parseError(res: Response): Promise<{ message: string; rawText: string; rawJson?: any }> {
  const rawText = await res.text();
  try {
    const json = JSON.parse(rawText) as ApiErrorShape;
    const fallback = json.message ?? `HTTP ${res.status}`;
    const message = formatFastApiDetail(json.detail, fallback);
    return { message, rawText, rawJson: json };
  } catch {
    return { message: rawText || `HTTP ${res.status}`, rawText };
  }
}

function isFormDataBody(body: any) {
  if (!body) return false;

  // works in most environments
  if (typeof FormData !== "undefined" && body instanceof FormData) return true;

  // React-Native FormData polyfill duck-typing
  // RN FormData usually has a private _parts array
  if (typeof body === "object" && Array.isArray(body._parts)) return true;

  // fallback: constructor name
  if (body?.constructor?.name === "FormData") return true;

  return false;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const isFormData = isFormDataBody(options.body);

  const headers: Record<string, string> = {
    ...(options.headers as any),
  };

  const hasContentType = Object.keys(headers).some(
    (k) => k.toLowerCase() === "content-type"
  );

  if (!isFormData && !hasContentType) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const { message, rawText, rawJson } = await parseError(res);
    console.error("❌ API ERROR", {
      url,
      status: res.status,
      statusText: res.statusText,
      method: options.method ?? "GET",
      requestBody: options.body,
      responseText: rawText,
      responseJson: rawJson,
      isFormData,
      sentHeaders: headers,
    });
    throw new Error(message);
  }

  // חשוב ל-204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  const contentType = res.headers.get("content-type") || "";

  if (!contentType.includes("application/json")) {
    return (await res.text()) as unknown as T;
  }

  return (await res.json()) as T;
}



export async function authFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  // 2. במקום getAccessToken הישן, אנחנו מושכים את הסשן מסופבייס
  const [sessionRes, homeId] = await Promise.all([
    supabase.auth.getSession(),
    getSelectedHomeId()
  ]);

  const token = sessionRes.data.session?.access_token;

  return apiFetch<T>(path, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      // הטוקן עכשיו מגיע ישירות מהסשן המנוהל של סופבייס
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(homeId ? { "X-Home-ID": homeId } : {}),
    },
  });
}
