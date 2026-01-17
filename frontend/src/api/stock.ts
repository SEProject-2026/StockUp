import { authFetch } from "@/src/api/client";
import { UnitType } from "../components/receipts/review/review.shared";

export type GeneralResponse<T> = {
  status: "success" | "error";
  message?: string;
  data?: T;
};

// ----------------------
// Enums (match backend)
// ----------------------

export type LocationType =
  | "FRIDGE"
  | "FREEZER"
  | "PANTRY"
  | "CLEANING"
  | "OTHER";

export type ExpirationType = "FRESH" | "GOING_TO_EXPIRE" | "EXPIRED";

// ----------------------
// DTOs (match backend EXACT)
// ----------------------

export type ProductItemDTO = {
  id: string;
  quantity: number;
  expiration_date: string | null; // "YYYY-MM-DD"
  location: LocationType;
  status: ExpirationType;

  // (Optional future improvement)
  // unit?: UnitType;
};

export type ProductDTO = {
  id: string;
  home_id: string;
  original_name: string;
  nickname?: string | null;
  barcode?: string | null;

  total_quantity: number;
  items: ProductItemDTO[];
};

// ----------------------
// Internal fetch wrapper
// ----------------------

function stockFetch<T>(homeId: string, path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(options.headers as any),
    "X-Home-ID": homeId,
  };

  const bodyIsString = typeof options.body === "string";
  const hasContentType = Object.keys(headers).some(
    (k) => k.toLowerCase() === "content-type"
  );

  if (bodyIsString && !hasContentType) {
    headers["Content-Type"] = "application/json";
  }

  return authFetch<T>(path, { ...options, headers });
}

// ----------------------
// Add / Get
// ----------------------

export type AddProductPayload = {
  name: string;
  quantity: number;
  expiration_date?: string | null; // "YYYY-MM-DD"
  barcode?: string | null;
  location?: LocationType;
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

// ----------------------
// Item-level updates
// ----------------------

export async function updateItemQuantity(
  homeId: string,
  productId: string,
  itemId: string,
  payload: { new_quantity: number }
) {
  return stockFetch<GeneralResponse<ProductDTO | null>>(
    homeId,
    `/stock/${productId}/items/${itemId}/quantity`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function updateItemExpiration(
  homeId: string,
  productId: string,
  itemId: string,
  payload: { new_date: string | null }
) {
  return stockFetch<GeneralResponse<ProductDTO>>(
    homeId,
    `/stock/${productId}/items/${itemId}/expiration`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function updateItemLocation(
  homeId: string,
  productId: string,
  itemId: string,
  payload: { location: LocationType }
) {
  return stockFetch<GeneralResponse<ProductDTO>>(
    homeId,
    `/stock/${productId}/items/${itemId}/location`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

// ----------------------
// Product-level nickname
// ----------------------

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

// ----------------------
// Remove item
// ----------------------

export async function removeItem(homeId: string, productId: string, itemId: string) {
  return stockFetch<GeneralResponse<ProductDTO | null>>(
    homeId,
    `/stock/${productId}/items/${itemId}`,
    { method: "DELETE" }
  );
}

// ----------------------
// Search & Filter (GET)
// ----------------------

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

// ----------------------
// Receipt scan (unchanged)
// ----------------------

export type Storagelocation =
  | "fridge"
  | "freezer"
  | "pantry"
  | "cleaning"
  | "other";

export type DetectedReceiptItemDTO = {
  barcode: string;
  name: string;
  quantity: number;
  unit: UnitType;
  storage_location?: Storagelocation | null;

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
    params.mimeType ??
    (fileName.endsWith(".pdf") ? "application/pdf" : "image/jpeg");

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

// ----------------------
// ✅ Add from receipt (UPDATED RESPONSE TYPES)
// ----------------------

export type ReceiptItemRequestDTO = {
  name: string;
  quantity: number; // float
  barcode?: string | null;
  expiration_date?: string | null; // "YYYY-MM-DD"
  location?: LocationType | null;
  nickname?: string | null;
  unit?: UnitType; // KG / GR / UNIT / ...
  weight?: number | null; 
};

export type AddReceiptRequest = {
  items: ReceiptItemRequestDTO[];
  chain?: string | null;
};

export type AddedReceiptItemDTO = {
  index: number; // index in request.items
  name: string;
  barcode?: string | null;

  detected_quantity: number;
  detected_unit: UnitType;

  product_id: string;
  item_id: string;

  stored_quantity: number;
  stored_unit: UnitType;
  
};

export type AddReceiptResponseData = {
  added_count: number;
  items: AddedReceiptItemDTO[]; 
};

export async function addReceipt(homeId: string, payload: AddReceiptRequest) {
  return authFetch<GeneralResponse<AddReceiptResponseData>>("/stock/add-receipt", {
    method: "POST",
    headers: {
      "X-Home-ID": homeId,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
