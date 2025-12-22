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

function stockFetch<T>(homeId: string, path: string, options: RequestInit = {}) {
  return authFetch<T>(path, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      "X-Home-ID": homeId,
    },
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
  return stockFetch<GeneralResponse<ProductDTO>>(homeId, `/stock/${productId}/quantity`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function updateProductExpiration(
  homeId: string,
  productId: string,
  payload: { old_date: string | null; new_date: string | null }
) {
  return stockFetch<GeneralResponse<ProductDTO>>(homeId, `/stock/${productId}/expiration`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function updateProductNickname(
  homeId: string,
  productId: string,
  payload: { nickname: string }
) {
function stockFetch<T>(homeId: string, path: string, options: RequestInit = {}) {
  return authFetch<T>(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
      "X-Home-ID": homeId,
    },
  });
}
}

export async function removeProduct(
  homeId: string,
  productId: string,
  expiration_date: string | null
) {
  const q = encodeURIComponent(expiration_date ?? "");
  return stockFetch<GeneralResponse<ProductDTO | null>>(homeId, `/stock/${productId}?expiration_date=${q}`, {
    method: "DELETE",
  });
}

// ----------------------
// Search & Filter (GET)
// ----------------------

export type LocationType = "FRIDGE" | "FREEZER" | "PANTRY"| "CLEANING_SUPPLIES" | "OTHER";
export type ExpirationType = "FRESH" | "GOING_TO_EXPIRE" | "EXPIRED";

export async function searchStock(homeId: string, query: string) {
  const q = encodeURIComponent(query);
  return stockFetch<GeneralResponse<ProductDTO[]>>(homeId, `/stock/search?query=${q}`, {
    method: "GET",
  });
}

export async function filterStockByLocation(homeId: string, location: LocationType) {
  const q = encodeURIComponent(location);
  return stockFetch<GeneralResponse<ProductDTO[]>>(homeId, `/stock/filter/location?location=${q}`, {
    method: "GET",
  });
}

export async function filterStockByExpiration(homeId: string, type: ExpirationType) {
  const q = encodeURIComponent(type);
  return stockFetch<GeneralResponse<ProductDTO[]>>(homeId, `/stock/filter/expiration?type=${q}`, {
    method: "GET",
  });
}

