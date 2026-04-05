import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { Alert } from "react-native";

import {
  // filterStockByExpiration,
  // filterStockByLocation,
  getAllStock,
  searchStock,
  updateProductNickname,
  updateItemExpiration,
  updateItemQuantity,
  removeItem,
  type ProductDTO,
  filterStock,
} from "@/src/api/stock";

import { useDebouncedValue } from "@/src/hooks/common/useDebouncedValue";

import {
  locationKey,
  StatusFilter,
  InventoryRow,
  dtoToRows,
  rowsSignature,
  statusFilterToExpirationType,
  locationToLocationType,
  LocationSectionVM,
  locationLabel,
} from "@/src/components/inventory/inventory.utils";
import type { location } from "@/src/context/inventory-context";

type LoadMode = "initial" | "soft";

let inventoryCache: Record<string, InventoryRow[]> = {};

export function useInventoryData(params: {
  homeId?: string;
  initiallocation: locationKey;
  hideTabs: boolean;
}) {
  const { homeId, initiallocation, hideTabs } = params;

  const [rows, setRows] = useState<InventoryRow[]>(
    homeId ? inventoryCache[homeId] || [] : []
  );

  const [initialLoading, setInitialLoading] = useState(
    !homeId || (inventoryCache[homeId] || []).length === 0
  );
  const [isSearching, setIsSearching] = useState(false);

  const [selectedTab, setSelectedTab] = useState<locationKey>(initiallocation);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [itemToEdit, setItemToEdit] = useState<InventoryRow | null>(null);

  const effectivelocation: locationKey = hideTabs ? initiallocation : selectedTab;
  const debouncedSearch = useDebouncedValue(search, 400);

  const requestSeqRef = useRef(0);
  const prevSigRef = useRef<string>(rowsSignature(rows));

  const loadInventory = useCallback(
    async (mode: LoadMode = "soft") => {
      if (!homeId) return;
      const mySeq = ++requestSeqRef.current;
      const q = debouncedSearch.trim();

      try {
        if (mode === "initial") setInitialLoading(true);
        else if (q.length > 0) setIsSearching(true);

        let products: ProductDTO[] = [];
        if (q.length >= 2 || statusFilter !== "all" || effectivelocation !== "all") {
          const expType = statusFilter === "all" ? null : statusFilterToExpirationType(statusFilter);
          const locType = effectivelocation === "all" ? null : locationToLocationType(effectivelocation);
          const res = await filterStock(homeId, q, locType, expType);
          products = res.data ?? [];
        } else {
          const res = await getAllStock(homeId);
          products = res.data ?? [];
        }

        if (mySeq !== requestSeqRef.current) return;

        const flat = products.flatMap(dtoToRows);
        
        setRows(flat);
        prevSigRef.current = rowsSignature(flat);
        
        if (!q && statusFilter === "all" && effectivelocation === "all") {
          inventoryCache[homeId] = flat;
        }
      } catch (e: any) {
        if (mySeq !== requestSeqRef.current) return;
        console.error("Load error:", e);
      } finally {
        if (mySeq === requestSeqRef.current) {
          setInitialLoading(false);
          setIsSearching(false);
        }
      }
    },
    [homeId, debouncedSearch, effectivelocation, statusFilter]
  );

  useEffect(() => {
    if (!homeId) return;
    loadInventory(inventoryCache[homeId] ? "soft" : "initial");
  }, [homeId, debouncedSearch, effectivelocation, statusFilter, loadInventory]);

  const changeQty = useCallback(
    async (itemId: string, delta: number) => {
      if (!homeId) return;
      const current = rows.find((r) => r.itemId === itemId);
      if (!current) return;

      const next = current.quantity + delta;
      if (next < 0) return;

      const nextRows = next === 0
        ? rows.filter((r) => r.itemId !== itemId)
        : rows.map((r) => (r.itemId === itemId ? { ...r, quantity: next } : r));

      setRows(nextRows);

      try {
        if (next === 0) {
          await removeItem(homeId, current.productId, itemId);
        } else {
          await updateItemQuantity(homeId, current.productId, itemId, { new_quantity: next });
        }
      } catch (e) {
        loadInventory("soft");
      }
    },
    [homeId, rows, loadInventory]
  );

  const deleteRow = useCallback(async (itemId: string) => {
    const item = rows.find(r => r.itemId === itemId);
    if (!item) return;
    await changeQty(itemId, -item.quantity);
  }, [rows, changeQty]);

const saveEdit = useCallback(async (itemId: string, updatedValues: { nickname?: string | null, quantity?: number, expirationDate?: string | null }) => {
  if (!homeId) return;
  const current = rows.find(r => r.itemId === itemId);
  if (!current) return;

  try {
    // 1. עדכון כינוי - אם המשתמש רוקן את השדה, נשלח "" כדי לאפס
    if (updatedValues.nickname !== undefined && updatedValues.nickname !== current.name) {
      const cleanNickname = updatedValues.nickname === null ? null : updatedValues.nickname.trim();
      await updateProductNickname(homeId, current.productId, { 
        nickname: cleanNickname // אם ריק, יחזור לשם המקורי
      });
    }

    // 2. עדכון כמות
    if (updatedValues.quantity !== undefined && updatedValues.quantity !== current.quantity) {
      if (updatedValues.quantity === 0) {
        await removeItem(homeId, current.productId, itemId);
      } else {
        await updateItemQuantity(homeId, current.productId, itemId, { 
          new_quantity: updatedValues.quantity 
        });
      }
    }

    // 3. עדכון תוקף
    if (updatedValues.expirationDate !== undefined && updatedValues.expirationDate !== current.expirationDate) {
      const cleanDate = updatedValues.expirationDate === null ? null : updatedValues.expirationDate.trim();
      await updateItemExpiration(homeId, current.productId, itemId, {
        new_date: cleanDate
      });
    }

    await loadInventory("soft");
    setItemToEdit(null);
  } catch (e) {
    console.error("Save error:", e);
    Alert.alert("שגיאה", "לא הצלחתי לשמור את השינויים");
  }
}, [homeId, rows, loadInventory]);

  const groupedSections = useMemo((): LocationSectionVM[] => {
    if (!rows || rows.length === 0) return [];

    // 1. Group by location then by product
    const locMap = new Map<location, Map<string, any>>();

    for (const r of rows) {
      if (!locMap.has(r.location)) {
        locMap.set(r.location, new Map());
      }
      const productMap = locMap.get(r.location)!;
      const key = `${r.productId}__${r.originalName}`;

      if (!productMap.has(key)) {
        productMap.set(key, {
          key: `${r.location}__${key}`, // key must be unique even if product appears in diff locations
          productId: r.productId,
          title: r.name,
          subtitle: r.hasNickname ? r.originalName : undefined,
          totalQuantity: 0,
          sections: [{ location: r.location, totalQuantity: 0, items: [] }]
        });
      }

      const g = productMap.get(key);
      g.totalQuantity += r.quantity;
      const sec = g.sections[0]; // in this mode, g always has exactly one section matching its parent location
      sec.totalQuantity += r.quantity;
      sec.items.push(r);
    }

    // 2. Transform to LocationSectionVM[]
    const result: LocationSectionVM[] = [];
    
    // Sort locations in a specific order if needed, but for now just all
    const allLocations: location[] = ["fridge", "freezer", "pantry", "cleaning", "other"];
    
    for (const loc of allLocations) {
      const productMap = locMap.get(loc);
      if (productMap && productMap.size > 0) {
        const products = Array.from(productMap.values())
          .map(g => ({
            ...g,
            sections: g.sections.map((sec: any) => ({
              ...sec,
              items: sec.items.sort((a: any, b: any) => (a.expirationDate ?? "9").localeCompare(b.expirationDate ?? "9"))
            }))
          }))
          .sort((a, b) => a.title.localeCompare(b.title, "he"));

        result.push({
          location: loc,
          label: locationLabel(loc),
          items: products
        });
      }
    }

    return result;
  }, [rows]);

  return {
    rows,
    initialLoading,
    isSearching,
    selectedTab,
    setSelectedTab,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    itemToEdit,
    setItemToEdit,
    loadInventory,
    changeQty,
    deleteRow,
    saveEdit,
    groupedItems: groupedSections,
  };
}