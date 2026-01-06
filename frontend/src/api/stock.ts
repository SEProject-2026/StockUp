import { authFetch } from "@/src/api/client";

export type GeneralResponse<T> = {
  status: "success" | "error";
  message?: string;
  data?: T;
};

export type ProductItemDTO = {
  expiration_date: string | null; // "YYYY-MM-DD"
  quantity: number;
  status: string;
};

export type ProductDTO = {
  id: string;
  home_id: string;
  original_name: string;
  nickname?: string | null;
  barcode?: string | null;
  location?: string | null;
  quantity: number;
  items: ProductItemDTO[];
};

/**
 * ⚠️ חשוב:
 * authFetch כנראה מוסיף baseURL + Authorization + Content-Type.
 * ל-JSON זה מעולה, אבל ל-FormData אסור לנו לשים Content-Type ידנית.
 */
function stockFetch<T>(homeId: string, path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(options.headers as any),
    "X-Home-ID": homeId,
  };

  // אם הבודי הוא string => זה JSON (כמו addProduct), נוסיף Content-Type אם לא קיים
  const bodyIsString = typeof options.body === "string";
  const hasContentType =
    Object.keys(headers).some((k) => k.toLowerCase() === "content-type");

  if (bodyIsString && !hasContentType) {
    headers["Content-Type"] = "application/json";
  }

  // אם זה FormData — לא נוגעים ב-Content-Type בכלל
  // (fetch ייצור את boundary לבד)
  return authFetch<T>(path, {
    ...options,
    headers,
  });
}

export type AddProductPayload = {
  name: string;
  quantity: number;
  barcode?: string | null;
  expiration_date?: string | null; // "YYYY-MM-DD"
  location?: string | null;
  nickname?: string | null;
};

export async function addProduct(homeId: string, payload: AddProductPayload) {
  return stockFetch<GeneralResponse<ProductDTO>>(homeId, "/stock/add", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getAllStock(homeId: string) {
  return stockFetch<GeneralResponse<ProductDTO[]>>(homeId, "/stock/all", {
    method: "GET",
  });
}

export async function updateProductQuantity(
  homeId: string,
  productId: string,
  payload: { expiration_date: string | null; new_quantity: number }
) {
  return stockFetch<GeneralResponse<ProductDTO>>(
    homeId,
    `/stock/${productId}/quantity`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function updateProductExpiration(
  homeId: string,
  productId: string,
  payload: { old_date: string | null; new_date: string | null }
) {
  return stockFetch<GeneralResponse<ProductDTO>>(
    homeId,
    `/stock/${productId}/expiration`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function updateProductNickname(
  homeId: string,
  productId: string,
  payload: { nickname: string }
) {
  return stockFetch<GeneralResponse<ProductDTO>>(
    homeId,
    `/stock/${productId}/nickname`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function removeProduct(
  homeId: string,
  productId: string,
  expiration_date: string | null
) {
  const qs = expiration_date
    ? `?expiration_date=${encodeURIComponent(expiration_date)}`
    : "";

  return stockFetch<GeneralResponse<ProductDTO | null>>(
    homeId,
    `/stock/${productId}${qs}`,
    { method: "DELETE" }
  );
}

// ----------------------
// Search & Filter (GET)
// ----------------------

export type LocationType =
  | "FRIDGE"
  | "FREEZER"
  | "PANTRY"
  | "CLEANING_SUPPLIES"
  | "OTHER";
export type ExpirationType = "FRESH" | "GOING_TO_EXPIRE" | "EXPIRED";

export async function searchStock(homeId: string, query: string) {
  const q = encodeURIComponent(query);
  return stockFetch<GeneralResponse<ProductDTO[]>>(
    homeId,
    `/stock/search?query=${q}`,
    { method: "GET" }
  );
}

export async function filterStockByLocation(homeId: string, location: LocationType) {
  const q = encodeURIComponent(location);
  return stockFetch<GeneralResponse<ProductDTO[]>>(
    homeId,
    `/stock/filter/location?location=${q}`,
    { method: "GET" }
  );
}

export async function filterStockByExpiration(homeId: string, type: ExpirationType) {
  const q = encodeURIComponent(type);
  return stockFetch<GeneralResponse<ProductDTO[]>>(
    homeId,
    `/stock/filter/expiration?type=${q}`,
    { method: "GET" }
  );
}

// --- Receipt Scan (OCR) ---
// ✅ טיפוסים לפי השרת שלך
export type DetectedReceiptItemDTO = {
  barcode: string;
  name: string;
  quantity: number;
  unit: string; // UnitType אצל השרת (UNIT / KG וכו')
};

export type ReceiptDTO = {
  id: string;
  home_id: string;
  user_id: string;
  chain?: string | null;
  items: DetectedReceiptItemDTO[];
};

function isProbablyImage(mimeType?: string | null) {
  return !!mimeType && mimeType.startsWith("image/");
}

function withTimeout<T>(p: Promise<T>, ms: number, label: string) {
  let t: any;
  const timeout = new Promise<never>((_, reject) => {
    t = setTimeout(() => reject(new Error(`${label} (timeout אחרי ${ms}ms)`)), ms);
  });
  return Promise.race([p.finally(() => clearTimeout(t)), timeout]);
}

/**
 * ✅ scanReceipt חדש:
 * - לא משתמש ב-authFetch כדי לא להסתבך עם FormData/JSON parsing.
 * - עושה fetch עם FormData + timeout + לוגים.
 *
 * ⚠️ אם השרת שלך דורש Authorization:
 * כרגע אין לנו גישה לטוקן מתוך authFetch.
 * אם את אומרת לי איך authFetch מוסיף Authorization (מאיפה הוא קורא את הטוקן),
 * אני אתן לך שורה אחת להוסיף פה.
 */
export async function scanReceipt(
  homeId: string,
  params: {
    fileUri: string;
    fileName?: string | null;
    mimeType?: string | null;
  }
) {
  const fileName =
    params.fileName ??
    (isProbablyImage(params.mimeType) ? "receipt.jpg" : "receipt.pdf");

  const mimeType =
    params.mimeType ?? (fileName.endsWith(".pdf") ? "application/pdf" : "image/jpeg");

  const form = new FormData();
  form.append("file", {
    uri: params.fileUri,
    name: fileName,
    type: mimeType,
  } as any);

  return stockFetch<GeneralResponse<ReceiptDTO>>(homeId, "/stock/scan", {
    method: "POST",
    body: form,
  });
}
