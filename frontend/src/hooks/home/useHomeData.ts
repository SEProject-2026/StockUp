import { useState, useCallback, useMemo } from "react";
import { Alert } from "react-native";
import { getAllStock, ProductDTO } from "@/src/api/stock";
import { location } from "@/src/context/inventory-context";

let cachedHomeData: Record<string, any[]> = {};

function locationToLocation(loc?: string | null): location {
  const l = (loc ?? "").toUpperCase();
  if (l === "FRIDGE") return "fridge";
  if (l === "FREEZER") return "freezer";
  if (l === "PANTRY") return "pantry";
  if (l === "CLEANING") return "cleaning";
  return "other";
}

function productDtoToHomeItems(dto: ProductDTO) {
  const displayName = dto.nickname?.trim() ? dto.nickname : dto.original_name;
  if (dto.items?.length) {
    return dto.items.map((it) => ({
      id: String(it.id),
      productId: String(dto.id),
      name: displayName,
      location: locationToLocation(it.location),
      quantity: it.quantity,
      expiresAt: it.expiration_date ?? undefined,
    }));
  }
  return [{
    id: `${dto.id}__fallback`,
    productId: String(dto.id),
    name: displayName,
    location: "other" as location,
    quantity: dto.total_quantity ?? 0,
    expiresAt: undefined,
  }];
}

export function useHomeData(homeId: string) {
  const [items, setItems] = useState<any[]>(cachedHomeData[homeId] || []);
  const [isLoading, setIsLoading] = useState(items.length === 0);

  const loadData = useCallback(async (forceRefresh = false) => {
    if (!homeId) return;

    if (items.length === 0) {
      setIsLoading(true);
    }

    try {
      const res = await getAllStock(homeId);
      const products = res.data ?? [];
      const normalized = products.flatMap(productDtoToHomeItems);
      
      setItems(normalized);
      cachedHomeData[homeId] = normalized;
    } catch (e: any) {
    } finally {
      setIsLoading(false);
    }
  }, [homeId]);

  const stats = useMemo(() => {
    const today = new Date().setHours(0, 0, 0, 0);
    const s = { 
      total: items.length, 
      fridge: 0, 
      freezer: 0, 
      pantry: 0, 
      cleaningSupplies: 0, 
      other: 0, 
      expiringSoon: 0 
    };
    
    items.forEach(item => {
      const loc = item.location;
      if (loc === 'fridge') s.fridge++;
      else if (loc === 'freezer') s.freezer++;
      else if (loc === 'pantry') s.pantry++;
      else if (loc === 'cleaning') s.cleaningSupplies++;
      else s.other++;
      
      if (item.expiresAt) {
        const diff = (new Date(item.expiresAt).getTime() - today) / (1000 * 60 * 60 * 24);
        if (diff >= 0 && diff <= 3) s.expiringSoon++;
      }
    });
    return s;
  }, [items]);

  const expiringSoon = useMemo(() => {
    return items
      .filter(i => i.expiresAt)
      .sort((a, b) => new Date(a.expiresAt).getTime() - new Date(b.expiresAt).getTime())
      .slice(0, 3);
  }, [items]);

  return { items, stats, expiringSoon, loadData, isLoading };
}