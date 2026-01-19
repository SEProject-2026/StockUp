import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert } from "react-native";

import {
  filterStockByExpiration,
  filterStockByLocation,
  getAllStock,
  searchStock,
  updateProductNickname,
  updateItemExpiration,
  updateItemQuantity,
  removeItem,
  type ProductDTO,
} from "@/src/api/stock";

import { useDebouncedValue } from "@/src/hooks/useDebouncedValue";

import {
  locationKey,
  StatusFilter,
  InventoryRow,
  ProductGroupVM,
  dtoToRows,
  rowsSignature,
  statusFilterToExpirationType,
  locationToLocationType,
  toIsoDateOnly,
} from "@/src/components/inventory/inventory.utils";

type LoadMode = "initial" | "soft";

export function useInventoryData(params: {
  homeId?: string;
  initiallocation: locationKey;
  hideTabs: boolean;
}) {
  const { homeId, initiallocation, hideTabs } = params;

  const [rows, setRows] = useState<InventoryRow[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);

  const [selectedTab, setSelectedTab] = useState<locationKey>(initiallocation);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [itemToEdit, setItemToEdit] = useState<InventoryRow | null>(null);

  const effectivelocation: locationKey = hideTabs ? initiallocation : selectedTab;
  const debouncedSearch = useDebouncedValue(search, 400);

  const requestSeqRef = useRef(0);
  const prevSigRef = useRef<string>("");
  const didInitialLoadRef = useRef<string | null>(null);

  const fetchProducts = useCallback(
    async (q: string, effCat: locationKey, sf: StatusFilter): Promise<ProductDTO[]> => {
      if (!homeId) return [];

      if (q.length >= 2) {
        const res = await searchStock(homeId, q);
        return res.data ?? [];
      }

      if (sf !== "all") {
        const expType = statusFilterToExpirationType(sf);
        // expType כאן לא null כי sf !== "all"
        const res = await filterStockByExpiration(homeId, expType!);
        return res.data ?? [];
      }

      if (effCat !== "all") {
        const loc = locationToLocationType(effCat);
        const res = await filterStockByLocation(homeId, loc);
        return res.data ?? [];
      }

      const res = await getAllStock(homeId);
      return res.data ?? [];
    },
    [homeId]
  );

  const applyClientFilters = useCallback(
    (input: InventoryRow[], q: string, effCat: locationKey, sf: StatusFilter) => {
      let out = input;

      // location tab filtering (UI)
      if (effCat !== "all") out = out.filter((r) => r.location === effCat);

      // search filtering
      if (q.length >= 2) {
        const qq = q.toLowerCase();
        out = out.filter(
          (r) =>
            r.name.toLowerCase().includes(qq) ||
            r.originalName.toLowerCase().includes(qq)
        );
      }

      // status filtering
      if (sf !== "all") {
        const wanted = statusFilterToExpirationType(sf)!;
        out = out.filter((r) => String(r.status ?? "").toUpperCase() === wanted);
      }

      return out;
    },
    []
  );

  const loadInventory = useCallback(
    async (mode: LoadMode = "soft") => {
      if (!homeId) return;

      const mySeq = ++requestSeqRef.current;
      const q = debouncedSearch.trim();

      try {
        if (mode === "initial") setInitialLoading(true);
        else setIsSearching(true);

        const products = await fetchProducts(q, effectivelocation, statusFilter);
        if (mySeq !== requestSeqRef.current) return;

        const flat = products.flatMap(dtoToRows);
        const filtered = applyClientFilters(flat, q, effectivelocation, statusFilter);

        const nextSig = rowsSignature(filtered);
        if (nextSig !== prevSigRef.current) {
          prevSigRef.current = nextSig;
          setRows(filtered);
        }
      } catch (e: any) {
        if (mySeq !== requestSeqRef.current) return;
        Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לטעון מלאי");
      } finally {
        if (mySeq === requestSeqRef.current) {
          setInitialLoading(false);
          setIsSearching(false);
        }
      }
    },
    [homeId, debouncedSearch, effectivelocation, statusFilter, fetchProducts, applyClientFilters]
  );

  useEffect(() => {
    if (homeId) return;

    setRows([]);
    prevSigRef.current = "";
    setInitialLoading(false);
    setIsSearching(false);
    didInitialLoadRef.current = null;
  }, [homeId]);

  useEffect(() => {
    if (!homeId) return;

    if (didInitialLoadRef.current !== homeId) {
      didInitialLoadRef.current = homeId;
      loadInventory("initial");
    }
  }, [homeId, loadInventory]);

  useEffect(() => {
    if (!homeId) return;
    if (didInitialLoadRef.current !== homeId) return;

    loadInventory("soft");
  }, [homeId, debouncedSearch, effectivelocation, statusFilter, loadInventory]);

  // ✅ NEW: group by PRODUCT (not by location+name)
  const groupedItems: ProductGroupVM[] = useMemo(() => {
    const productMap = new Map<
      string,
      {
        key: string;
        productId: string;
        title: string;
        subtitle?: string;
        originalName: string;
        nickname?: string | null;
        totalQuantity: number;
        byLoc: Map<string, { location: InventoryRow["location"]; totalQuantity: number; items: InventoryRow[] }>;
      }
    >();

    for (const r of rows) {
      // separation rule: even if nickname same, do NOT merge different originalName
      // productId is unique anyway, but originalName is part of your "identity" requirement.
      const key = `${r.productId}__${r.originalName}`;

      const g =
        productMap.get(key) ??
        (() => {
          const hasNick = r.hasNickname;
          const title = r.name; // already displayName (nickname or original)
          const subtitle = hasNick ? r.originalName : undefined;

          const fresh = {
            key,
            productId: r.productId,
            title,
            subtitle,
            originalName: r.originalName,
            nickname: hasNick ? title : null,
            totalQuantity: 0,
            byLoc: new Map<
              string,
              { location: InventoryRow["location"]; totalQuantity: number; items: InventoryRow[] }
            >(),
          };
          productMap.set(key, fresh);
          return fresh;
        })();

      g.totalQuantity += r.quantity;

      const locKey = r.location;
      const sec =
        g.byLoc.get(locKey) ??
        (() => {
          const created = { location: r.location, totalQuantity: 0, items: [] as InventoryRow[] };
          g.byLoc.set(locKey, created);
          return created;
        })();

      sec.totalQuantity += r.quantity;
      sec.items.push(r);
    }

    const groups: ProductGroupVM[] = Array.from(productMap.values()).map((g) => {
      // sections sorted by: fridge, freezer, pantry, cleaning, other
      const order: Record<string, number> = { fridge: 1, freezer: 2, pantry: 3, cleaning: 4, other: 5 };

      const sections = Array.from(g.byLoc.values())
        .sort((a, b) => (order[a.location] ?? 99) - (order[b.location] ?? 99))
        .map((sec) => ({
          location: sec.location,
          totalQuantity: sec.totalQuantity,
          items: sec.items
            .slice()
            .sort((a, b) => (a.expirationDate ?? "9999-12-31").localeCompare(b.expirationDate ?? "9999-12-31")),
        }));

      return {
        key: g.key,
        productId: g.productId,
        title: g.title,
        subtitle: g.subtitle,
        originalName: g.originalName,
        nickname: g.nickname,
        totalQuantity: g.totalQuantity,
        sections,
      };
    });

    return groups.sort((a, b) => a.title.localeCompare(b.title, "he"));
  }, [rows]);

  const changeQty = useCallback(
  async (itemId: string, delta: number) => {
    if (!homeId) return;

    const current = rows.find((r) => r.itemId === itemId || r.id === itemId);
    if (!current) return;

    const next = current.quantity + delta;
    if (next < 0) return;

    if (next === 0) {
      const optimistic = rows.filter((r) => r.itemId !== current.itemId);
      setRows(optimistic);
      prevSigRef.current = rowsSignature(optimistic);

      try {
        await removeItem(homeId, current.productId, current.itemId);
      } catch (e: any) {
        Alert.alert("שגיאה", e?.message ?? "לא הצלחתי למחוק פריט");
        await loadInventory("soft");
      }
      return;
    }

    const optimistic = rows.map((r) => (r.itemId === current.itemId ? { ...r, quantity: next } : r));
    setRows(optimistic);
    prevSigRef.current = rowsSignature(optimistic);

    try {
      await updateItemQuantity(homeId, current.productId, current.itemId, {
        new_quantity: next,
      });
    } catch (e: any) {
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לעדכן כמות");
      await loadInventory("soft");
    }
  },
  [homeId, rows, loadInventory]
);

  const deleteRow = useCallback(
    (itemId: string) => {
      if (!homeId) return;

      const current = rows.find((r) => r.itemId === itemId || r.id === itemId);
      if (!current) return;

      Alert.alert("מחיקה", `למחוק את "${current.name}"?`, [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: async () => {
            try {
              await removeItem(homeId, current.productId, current.itemId);

              const nextRows = rows.filter((r) => r.itemId !== current.itemId);
              setRows(nextRows);
              prevSigRef.current = rowsSignature(nextRows);
            } catch (e: any) {
              Alert.alert("שגיאה", e?.message ?? "לא הצלחתי למחוק");
              await loadInventory("soft");
            }
          },
        },
      ]);
    },
    [homeId, rows, loadInventory]
  );

  const saveEdit = useCallback(
    async (itemId: string, values: { name: string; quantity: number; expiresAt?: string }) => {
      if (!homeId) return;

      const current = rows.find((r) => r.itemId === itemId || r.id === itemId);
      if (!current) return;

      const newDisplayName = values.name.trim();
      const newQty = values.quantity;
      const newExp = toIsoDateOnly(values.expiresAt ?? null);

      try {
        if (newDisplayName && newDisplayName !== current.name) {
          await updateProductNickname(homeId, current.productId, { nickname: newDisplayName });
        }

        if (newExp !== current.expirationDate) {
          await updateItemExpiration(homeId, current.productId, current.itemId, {
            new_date: newExp,
          });
        }

        if (newQty !== current.quantity) {
          if (newQty === 0) {
            await removeItem(homeId, current.productId, current.itemId);

            const nextRows = rows.filter((r) => r.itemId !== current.itemId);
            setRows(nextRows);
            prevSigRef.current = rowsSignature(nextRows);

            setItemToEdit(null);
            return;
          }

          await updateItemQuantity(homeId, current.productId, current.itemId, {
            new_quantity: newQty,
          });
        }

        if (newQty !== current.quantity) {
          await updateItemQuantity(homeId, current.productId, current.itemId, {
            new_quantity: newQty,
          });
        }

        setItemToEdit(null);
        await loadInventory("soft");
      } catch (e: any) {
        Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לשמור שינויים");
      }
    },
    [homeId, rows, loadInventory]
  );

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
