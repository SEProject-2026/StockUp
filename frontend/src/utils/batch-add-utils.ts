import { CatalogItem } from "@/src/api/catalog";

export function uid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

export function normalizeCatalogList(raw: any): CatalogItem[] {
  const arr = Array.isArray(raw) ? raw : (raw?.items || raw?.results || []);
  return arr
    .map((x: any) => ({
      name: x.name ?? x.product_name ?? x.original_name ?? "",
      barcode: x.barcode ?? x.code ?? null,
      brand: x.brand ?? null,
      chain: x.chain ?? null,
    }))
    .filter((x: CatalogItem) => x.name);
}

export function normalizeCatalogOne(raw: any): CatalogItem | null {
  if (!raw) return null;
  const name = raw.name ?? raw.product_name ?? raw.original_name ?? "";
  if (!name) return null;
  return {
    name,
    barcode: raw.barcode ?? raw.code ?? null,
    brand: raw.brand ?? null,
    chain: raw.chain ?? null,
  };
}