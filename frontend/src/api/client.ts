import { API_BASE_URL } from "@/src/config/api";
import { getAccessToken } from "@/src/auth/token";
import { getSelectedHomeId } from "@/app/home/selected-home";

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

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    const { message, rawText, rawJson } = await parseError(res);

    // ✅ פה למקם: לוג מרכזי לכל הבעיות (422/401/500 וכו')
    console.error("❌ API ERROR", {
      url,
      status: res.status,
      statusText: res.statusText,
      method: options.method ?? "GET",
      requestBody: options.body,
      responseText: rawText,
      responseJson: rawJson,
    });

    throw new Error(message);
  }

  // אם יש endpoints שמחזירים 204 / גוף ריק
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await res.text()) as unknown as T;
  }

  return (await res.json()) as T;
}

export async function authFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const [token, homeId] = await Promise.all([getAccessToken(), getSelectedHomeId()]);

  return apiFetch<T>(path, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(homeId ? { "X-Home-ID": homeId } : {}),
    },
  });
}
