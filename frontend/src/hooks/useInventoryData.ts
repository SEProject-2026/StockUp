import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert } from "react-native";

import {
  filterStockByExpiration,
  filterStockByLocation,
  getAllStock,
  removeProduct,
  searchStock,
  updateProductExpiration,
  updateProductNickname,
  updateProductQuantity,
  type ProductDTO,
} from "@/src/api/stock";

import { useDebouncedValue } from "@/src/hooks/useDebouncedValue";

import {
  CategoryKey,
  StatusFilter,
  InventoryRow,
  categoryToLocationType,
  dtoToRows,
  rowsSignature,
  statusFilterToExpirationType,
  toIsoDateOnly,
} from "@/src/components/inventory/inventory.utils";

type LoadMode = "initial" | "soft";

export function useInventoryData(params: {
  homeId?: string;
  initialCategory: CategoryKey;
  hideTabs: boolean;
}) {
  const { homeId, initialCategory, hideTabs } = params;

  const [rows, setRows] = useState<InventoryRow[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);

  const [selectedTab, setSelectedTab] = useState<CategoryKey>(initialCategory);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [itemToEdit, setItemToEdit] = useState<InventoryRow | null>(null);

  const effectiveCategory: CategoryKey = hideTabs ? initialCategory : selectedTab;

  const debouncedSearch = useDebouncedValue(search, 400);

  const requestSeqRef = useRef(0);

  const prevSigRef = useRef<string>("");

  const didInitialLoadRef = useRef<string | null>(null);

  const fetchProducts = useCallback(
    async (q: string, effCat: CategoryKey, sf: StatusFilter): Promise<ProductDTO[]> => {
      if (!homeId) return [];

      if (q.length >= 2) {
        const res = await searchStock(homeId, q);
        return res.data ?? [];
      }

      if (sf !== "all") {
        const expType = statusFilterToExpirationType(sf);
        const res = await filterStockByExpiration(homeId, expType);
        return res.data ?? [];
      }

      if (effCat !== "all") {
        const loc = categoryToLocationType(effCat);
        const res = await filterStockByLocation(homeId, loc);
        return res.data ?? [];
      }

      const res = await getAllStock(homeId);
      return res.data ?? [];
    },
    [homeId]
  );

  const applyClientFilters = useCallback(
    (input: InventoryRow[], q: string, effCat: CategoryKey, sf: StatusFilter) => {
      let out = input;

      if (effCat !== "all") out = out.filter((r) => r.category === effCat);

      if (q.length >= 2) {
        const qq = q.toLowerCase();
        out = out.filter(
          (r) =>
            r.name.toLowerCase().includes(qq) ||
            r.originalName.toLowerCase().includes(qq)
        );
      }

      if (sf !== "all") {
        const wanted = statusFilterToExpirationType(sf);
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

        const products = await fetchProducts(q, effectiveCategory, statusFilter);
        if (mySeq !== requestSeqRef.current) return;

        const flat = products.flatMap(dtoToRows);
        const filtered = applyClientFilters(flat, q, effectiveCategory, statusFilter);

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
    [
      homeId,
      debouncedSearch,
      effectiveCategory,
      statusFilter,
      fetchProducts,
      applyClientFilters,
    ]
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
  }, [homeId, debouncedSearch, effectiveCategory, statusFilter, loadInventory]);

  const groupedItems = useMemo(() => {
    const map = new Map<
      string,
      {
        key: string;
        name: string;
        category: InventoryRow["category"];
        totalQuantity: number;
        items: InventoryRow[];
      }
    >();

    for (const r of rows) {
      const key = `${r.category}__${r.name}`;

      const g =
        map.get(key) ?? {
          key,
          name: r.name,
          category: r.category,
          totalQuantity: 0,
          items: [] as InventoryRow[],
        };

      g.totalQuantity += r.quantity;
      g.items.push(r);
      map.set(key, g);
    }

    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name, "he"));
  }, [rows]);

  const changeQty = useCallback(
    async (rowId: string, delta: number) => {
      if (!homeId) return;

      const current = rows.find((r) => r.id === rowId);
      if (!current) return;

      const next = current.quantity + delta;
      if (next < 0) return;

      const optimistic = rows.map((r) => (r.id === rowId ? { ...r, quantity: next } : r));
      setRows(optimistic);
      prevSigRef.current = rowsSignature(optimistic);

      try {
        await updateProductQuantity(homeId, current.productId, {
          expiration_date: current.expirationDate,
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
    (rowId: string) => {
      if (!homeId) return;

      const current = rows.find((r) => r.id === rowId);
      if (!current) return;

      Alert.alert("מחיקה", `למחוק את "${current.name}"?`, [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: async () => {
            try {
              await removeProduct(homeId, current.productId, current.expirationDate);

              const nextRows = rows.filter((r) => r.id !== rowId);
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
    async (rowId: string, values: { name: string; quantity: number; expiresAt?: string }) => {
      if (!homeId) return;

      const current = rows.find((r) => r.id === rowId);
      if (!current) return;

      const newName = values.name.trim();
      const newQty = values.quantity;
      const newExp = toIsoDateOnly(values.expiresAt ?? null);
      const oldExp = current.expirationDate;

      try {
        if (newName && newName !== current.name) {
          await updateProductNickname(homeId, current.productId, { nickname: newName });
        }

        if (newExp !== oldExp) {
          await updateProductExpiration(homeId, current.productId, {
            old_date: oldExp,
            new_date: newExp,
          });
        }

        if (newQty !== current.quantity) {
          await updateProductQuantity(homeId, current.productId, {
            expiration_date: newExp,
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
