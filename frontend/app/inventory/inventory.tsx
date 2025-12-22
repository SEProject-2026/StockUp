// app/inventory/index.tsx (או איפה שנמצא InventoryScreen שלך)
import React, { useCallback, useMemo, useState } from "react";
import { View, StyleSheet, Alert, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams, useFocusEffect } from "expo-router";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";

import { InventoryFiltersBar } from "@/src/components/inventory/InventoryFiltersBar";
import { GroupedInventoryList } from "@/src/components/inventory/GroupedInventoryList";
import { EditItemModal } from "@/src/components/inventory/EditItemModal";

import { Category, InventoryItem } from "@/src/context/inventory-context";

import {
  getAllStock,
  searchStock,
  filterStockByLocation,
  filterStockByExpiration,
  updateProductQuantity,
  updateProductExpiration,
  updateProductNickname,
  removeProduct,
  type ProductDTO,
  type LocationType,
  type ExpirationType,
} from "@/src/api/stock";

type InventoryRow = InventoryItem & {
  productId: string;
  expirationDate: string | null; // חשוב לשרת
  originalName: string;
  status?: string; // ExpirationType מהשרת
};

type CategoryKey = Category | "all";
type StatusFilter = "all" | "soon" | "expired";

function mapLocationToCategory(location?: string | null): Category {
  switch ((location ?? "").toUpperCase()) {
    case "FRIDGE":
      return "fridge";
    case "FREEZER":
      return "freezer";
    case "PANTRY":
      return "pantry";
    default:
      return "pantry";
  }
}

function categoryToLocationType(cat: Category): LocationType {
  switch (cat) {
    case "fridge":
      return "FRIDGE";
    case "freezer":
      return "FREEZER";
    case "pantry":
      return "PANTRY";
    default:
      return "PANTRY";
  }
}

function statusFilterToExpirationType(sf: StatusFilter): ExpirationType {
  // התאמה לשמות השרת אצלך
  if (sf === "soon") return "GOING_TO_EXPIRE";
  return "EXPIRED";
}

function toIsoDateOnly(s?: string | null) {
  if (!s) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  const d = new Date(s);
  if (Number.isNaN(+d)) return null;
  return d.toISOString().slice(0, 10);
}

function dtoToRows(dto: ProductDTO): InventoryRow[] {
  const displayName = dto.nickname?.trim() ? dto.nickname : dto.original_name;

  if (dto.items?.length) {
    return dto.items.map((it) => {
      const exp = it.expiration_date ? String(it.expiration_date) : null;

      return {
        id: `${dto.id}__${exp ?? "none"}`, // rowId
        name: displayName,
        quantity: it.quantity,
        category: mapLocationToCategory(dto.location),
        expiresAt: exp ?? undefined,
        productId: String(dto.id),
        expirationDate: exp,
        originalName: dto.original_name,
        status: it.status,
      };
    });
  }

  // fallback אם אין items
  return [
    {
      id: `${dto.id}__none`,
      name: displayName,
      quantity: dto.quantity ?? 0,
      category: mapLocationToCategory(dto.location),
      expiresAt: undefined,
      productId: String(dto.id),
      expirationDate: null,
      originalName: dto.original_name,
    },
  ];
}

export function InventoryScreenBase({
  initialCategory = "all",
  title = "מלאי",
  hideTabs = false,
}: {
  initialCategory?: CategoryKey;
  title?: string;
  hideTabs?: boolean;
}) {
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const currentHomeId = homeId ? String(homeId) : undefined;

  const [rows, setRows] = useState<InventoryRow[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedTab, setSelectedTab] = useState<CategoryKey>(initialCategory);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [itemToEdit, setItemToEdit] = useState<InventoryRow | null>(null);

  const effectiveCategory: CategoryKey = hideTabs ? initialCategory : selectedTab;

  // ✅ מבצע קריאה לשרת לפי הפילטרים שבמסך
  const loadInventory = useCallback(async () => {
    if (!currentHomeId) {
      setRows([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      const q = search.trim();
      let products: ProductDTO[] = [];

      // עדיפות: Search > Expiration > Location > All
      if (q) {
        const res = await searchStock(currentHomeId, q);
        products = res.data ?? [];
      } else if (statusFilter !== "all") {
        const expType = statusFilterToExpirationType(statusFilter);
        const res = await filterStockByExpiration(currentHomeId, expType);
        products = res.data ?? [];
      } else if (effectiveCategory !== "all") {
        const loc = categoryToLocationType(effectiveCategory);
        const res = await filterStockByLocation(currentHomeId, loc);
        products = res.data ?? [];
      } else {
        const res = await getAllStock(currentHomeId);
        products = res.data ?? [];
      }

      // המר ל-rows
      let newRows = products.flatMap(dtoToRows);

      // פילטרים “משלימים” מקומיים (כי בשרת אין קומבינציה של פילטרים)
      if (effectiveCategory !== "all") {
        newRows = newRows.filter((r) => r.category === effectiveCategory);
      }

      if (q) {
        const qq = q.toLowerCase();
        newRows = newRows.filter(
          (r) =>
            r.name.toLowerCase().includes(qq) ||
            r.originalName.toLowerCase().includes(qq)
        );
      }

      if (statusFilter !== "all") {
        const wanted = statusFilterToExpirationType(statusFilter);
        newRows = newRows.filter((r) => String(r.status ?? "").toUpperCase() === wanted);
      }

      setRows(newRows);
    } catch (e: any) {
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לטעון מלאי");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [currentHomeId, effectiveCategory, search, statusFilter]);

  // ✅ טוען בכל כניסה למסך
  useFocusEffect(
    React.useCallback(() => {
      loadInventory();
    }, [loadInventory])
  );

  const groupedItems = useMemo(() => {
    // כאן כבר לא חייבים לסנן שוב, אבל אפשר להשאיר קיבוץ בלבד
    const map = new Map<
      string,
      { key: string; name: string; category: Category; totalQuantity: number; items: InventoryRow[] }
    >();

    for (const r of rows) {
      const key = `${r.name}__${r.category}`;
      const g =
        map.get(key) ?? { key, name: r.name, category: r.category, totalQuantity: 0, items: [] as InventoryRow[] };
      g.totalQuantity += r.quantity;
      g.items.push(r);
      map.set(key, g);
    }

    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name, "he"));
  }, [rows]);

  const handleChangeQty = useCallback(
    async (rowId: string, delta: number) => {
      if (!currentHomeId) return;
      const current = rows.find((r) => r.id === rowId);
      if (!current) return;

      const next = current.quantity + delta;
      if (next < 0) return;

      setRows((prev) => prev.map((r) => (r.id === rowId ? { ...r, quantity: next } : r)));

      try {
        await updateProductQuantity(currentHomeId, current.productId, {
          expiration_date: current.expirationDate,
          new_quantity: next,
        });
      } catch (e: any) {
        Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לעדכן כמות");
        await loadInventory();
      }
    },
    [currentHomeId, rows, loadInventory]
  );

  const handleDelete = useCallback(
    (rowId: string) => {
      if (!currentHomeId) return;
      const current = rows.find((r) => r.id === rowId);
      if (!current) return;

      Alert.alert("מחיקה", `למחוק את "${current.name}"?`, [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: async () => {
            try {
              await removeProduct(currentHomeId, current.productId, current.expirationDate);
              setRows((prev) => prev.filter((r) => r.id !== rowId));
            } catch (e: any) {
              Alert.alert("שגיאה", e?.message ?? "לא הצלחתי למחוק");
              await loadInventory();
            }
          },
        },
      ]);
    },
    [currentHomeId, rows, loadInventory]
  );

  const handleSaveEdit = useCallback(
    async (rowId: string, values: { name: string; quantity: number; expiresAt?: string }) => {
      if (!currentHomeId) return;

      const current = rows.find((r) => r.id === rowId);
      if (!current) return;

      const newName = values.name.trim();
      const newQty = values.quantity;
      const newExp = toIsoDateOnly(values.expiresAt ?? null);
      const oldExp = current.expirationDate;

      try {
        if (newName && newName !== current.name) {
          await updateProductNickname(currentHomeId, current.productId, { nickname: newName });
        }

        if (newExp !== oldExp) {
          await updateProductExpiration(currentHomeId, current.productId, {
            old_date: oldExp,
            new_date: newExp,
          });
        }

        if (newQty !== current.quantity) {
          await updateProductQuantity(currentHomeId, current.productId, {
            expiration_date: newExp,
            new_quantity: newQty,
          });
        }

        setItemToEdit(null);
        await loadInventory();
      } catch (e: any) {
        Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לשמור שינויים");
      }
    },
    [currentHomeId, rows, loadInventory]
  );

  const handleBack = () => {
    if (currentHomeId) router.replace({ pathname: "/home/[homeId]", params: { homeId: currentHomeId } });
    else router.back();
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#F4F4F4", "#D7F0FF"]}
        start={{ x: 0.5, y: 0.2 }}
        end={{ x: 0.5, y: 0 }}
        style={styles.gradientBackground}
        pointerEvents="none"
      />

      <View style={{ flex: 1 }}>
        <ScreenHeader title={title} onBack={handleBack} />

        {!currentHomeId || loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#0284C7" />
          </View>
        ) : (
          <>
            <InventoryFiltersBar
              hideTabs={hideTabs}
              selectedTab={selectedTab}
              onChangeTab={setSelectedTab}
              search={search}
              onChangeSearch={setSearch}
              statusFilter={statusFilter}
              onChangeStatusFilter={setStatusFilter}
              filtersVisible={true}
            />

            <GroupedInventoryList
              groupedItems={groupedItems as any}
              onChangeQty={handleChangeQty}
              onEditItem={(it: any) => setItemToEdit(it)}
              onDeleteItem={handleDelete}
              onAddItem={() =>
                router.push({
                  pathname: "/inventory/add-item",
                  params: currentHomeId ? { homeId: currentHomeId } : {},
                })
              }
            />

            <BottomNavBar activeTab="inventory" />
          </>
        )}
      </View>

      <EditItemModal
        visible={!!itemToEdit}
        item={itemToEdit as any}
        onClose={() => setItemToEdit(null)}
        onSave={handleSaveEdit}
      />
    </SafeAreaView>
  );
}

export default function InventoryScreen() {
  return <InventoryScreenBase initialCategory="all" title="מלאי" hideTabs={false} />;
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F4F4" },
  gradientBackground: { ...StyleSheet.absoluteFillObject },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
});
