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

import { useDebouncedValue } from "@/src/hooks/useDebouncedValue";

import {
  locationKey,
  StatusFilter,
  InventoryRow,
  dtoToRows,
  rowsSignature,
  statusFilterToExpirationType,
  locationToLocationType,
} from "@/src/components/inventory/inventory.utils";

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

        // הפיכת ה-DTO לשורות שטוחות (InventoryRow)
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

  const groupedItems = useMemo(() => {
    if (!rows || rows.length === 0) return [];

    const productMap = new Map<string, any>();

    for (const r of rows) {
      // מפתח ייחודי לפי שם מוצר מקורי (כדי לאחד כפילויות)
      const key = `${r.productId}__${r.originalName}`;
      
      if (!productMap.has(key)) {
        productMap.set(key, {
          key,
          productId: r.productId,
          title: r.name,
          subtitle: r.hasNickname ? r.originalName : undefined,
          totalQuantity: 0,
          byLoc: new Map(),
        });
      }

      const g = productMap.get(key);
      g.totalQuantity += r.quantity;

      if (!g.byLoc.has(r.location)) {
        g.byLoc.set(r.location, { location: r.location, totalQuantity: 0, items: [] });
      }

      const sec = g.byLoc.get(r.location);
      sec.totalQuantity += r.quantity;
      sec.items.push(r);
    }

    return Array.from(productMap.values()).map(g => ({
      ...g,
      sections: Array.from(g.byLoc.values()).map((sec: any) => ({
        ...sec,
        items: sec.items.sort((a: any, b: any) => (a.expirationDate ?? "9").localeCompare(b.expirationDate ?? "9"))
      }))
    })).sort((a, b) => a.title.localeCompare(b.title, "he"));
  }, [rows]);

  return {
    rows,
    groupedItems,
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
  };
}