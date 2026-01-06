import { authFetch } from "@/src/api/client"; 
export type GeneralResponse<T> = {
  status: string;
  message?: string;
  data: T;
};

export type CatalogItem = {
  name: string;
  barcode?: string | null;
  brand?: string | null;
  chain?: string | null;
};

export async function searchCatalog(query: string) {
  return authFetch<GeneralResponse<CatalogItem[]>>(
    `/stock/catalog/search?query=${encodeURIComponent(query)}`
  );
}

export async function getCatalogByBarcode(barcode: string, chain?: string) {
  const qs = chain ? `?chain=${encodeURIComponent(chain)}` : "";
  return authFetch<GeneralResponse<CatalogItem>>(
    `/stock/catalog/barcode/${encodeURIComponent(barcode)}${qs}`
  );
}
