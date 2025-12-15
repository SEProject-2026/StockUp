
import React, { useMemo, useState } from "react";
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient"; 
import { useInventory, Category, InventoryItem } from "../../src/context/inventory-context";
import BottomNavBar from "@/src/layout/BottomNavBar";

import { InventoryFiltersBar } from "@/src/components/inventory/InventoryFiltersBar";
import { GroupedInventoryList } from "@/src/components/inventory/GroupedInventoryList";
import { EditItemModal } from "@/src/components/inventory/EditItemModal";
import ScreenHeader from "@/src/layout/ScreenHeader";

export type CategoryKey = Category | "all";
type StatusFilter = "all" | "soon" | "expired";

export type InventoryStats = {
  total: number;
  fridge: number;
  freezer: number;
  pantry: number;
  expiringSoon: number;
};

export type GroupedInventory = {
  key: string;
  name: string;
  category: Category;
  totalQuantity: number;
  items: InventoryItem[];
};

type InventoryScreenBaseProps = {
  initialCategory: CategoryKey;
  hideTabs?: boolean;
  title: string;
};

export function InventoryScreenBase({
  initialCategory,
  hideTabs,
  title,
}: InventoryScreenBaseProps) {
  const { items, updateItem, removeItem } = useInventory();

  const [selectedTab, setSelectedTab] = useState<CategoryKey>(initialCategory);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [filtersVisible, setFiltersVisible] = useState(false);

  const [itemToEdit, setItemToEdit] = useState<InventoryItem | null>(null);

  const effectiveCategory: CategoryKey = hideTabs ? initialCategory : selectedTab;

  const { groupedItems /*, stats*/ } = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let fridge = 0;
    let freezer = 0;
    let pantry = 0;
    let expiringSoon = 0;

    const filtered = items.filter((item) => {
      if (effectiveCategory !== "all" && item.category !== effectiveCategory) {
        return false;
      }

      if (search && !item.name.includes(search)) {
        return false;
      }

      if (statusFilter !== "all") {
        if (!item.expiresAt) return false;

        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffDays =
          (exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);

        //expiring soon = 0-3 days
        //will be user choice later
        if (statusFilter === "soon" && !(diffDays >= 0 && diffDays <= 3)) {
          return false;
        }
        if (statusFilter === "expired" && !(diffDays < 0)) {
          return false;
        }
      }

      return true;
    });

    items.forEach((item) => {
      if (item.category === "fridge") fridge++;
      if (item.category === "freezer") freezer++;
      if (item.category === "pantry") pantry++;

      if (item.expiresAt) {
        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffMs = exp.getTime() - today.getTime();
        const diffDays = diffMs / (1000 * 60 * 60 * 24);
        if (diffDays >= 0 && diffDays <= 3) {
          expiringSoon++;
        }
      }
    });

    const groupMap = new Map<string, GroupedInventory>();

    filtered.forEach((item) => {
      const key = `${item.name}__${item.category}`;
      let group = groupMap.get(key);
      if (!group) {
        group = {
          key,
          name: item.name,
          category: item.category,
          totalQuantity: 0,
          items: [],
        };
        groupMap.set(key, group);
      }
      group.totalQuantity += item.quantity;
      group.items.push(item);
    });

    const groupedItems = Array.from(groupMap.values()).sort((a, b) =>
      a.name.localeCompare(b.name, "he")
    );

    return {
      groupedItems,
    };
  }, [items, effectiveCategory, search, statusFilter]);

  const handleChangeQty = (id: string, delta: number) => {
    const current = items.find((it) => it.id === id);
    if (!current) return;
    const next = current.quantity + delta;
    if (next < 1) return;
    updateItem(id, { quantity: next });
  };

  const handleDelete = (id: string) => {
    const current = items.find((it) => it.id === id);
    Alert.alert(
      "מחיקת מוצר",
      `למחוק את "${current?.name ?? "המוצר"}" מהמלאי?`,
      [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: () => removeItem(id),
        },
      ]
    );
  };

  const handleSaveEdit = (
    id: string,
    values: { name: string; quantity: number; expiresAt?: string }
  ) => {
    updateItem(id, {
      name: values.name,
      quantity: values.quantity,
      expiresAt: values.expiresAt,
    });
    setItemToEdit(null);
  };

  const handleBack = () => {
    if (router.canGoBack && router.canGoBack()) {
      router.back();
    } else {
      router.replace("/");
    }
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

      <View style={styles.main}>
        {/* HEADER */}
        <ScreenHeader
          title={title}
          onBack={handleBack}
          rightSlot={
            <TouchableOpacity
              style={styles.headerIconButton}
              onPress={() => setFiltersVisible(prev => !prev)}
            >
              <Ionicons
                name={filtersVisible ? "options" : "filter-outline"}
                size={20}
                color="#111827"
              />
            </TouchableOpacity>
          }
        />

        {/* Tabs + (optionally) filters panel */}
        <InventoryFiltersBar
          hideTabs={hideTabs}
          selectedTab={selectedTab}
          onChangeTab={setSelectedTab}
          search={search}
          onChangeSearch={setSearch}
          statusFilter={statusFilter}
          onChangeStatusFilter={setStatusFilter}
        filtersVisible={filtersVisible}
        />

        {/* Grouped list */}
        <GroupedInventoryList
          groupedItems={groupedItems}
          onChangeQty={handleChangeQty}
          onEditItem={setItemToEdit}
          onDeleteItem={handleDelete}
          onAddItem={() => router.push("/inventory/add-item")}
        />

        <BottomNavBar activeTab="inventory" />
      </View>

      {/* Edit modal */}
      <EditItemModal
        visible={!!itemToEdit}
        item={itemToEdit}
        onClose={() => setItemToEdit(null)}
        onSave={handleSaveEdit}
      />
    </SafeAreaView>
  );
}

export default function InventoryScreen() {
  return (
    <InventoryScreenBase
      initialCategory="all"
      title="מלאי"
      hideTabs={false}
    />
  );
}

/* ---------- STYLES  ---------- */

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F4F4F4", 
  },
  gradientBackground: {
    ...StyleSheet.absoluteFillObject,
  },
  main: {
    flex: 1,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  headerIconButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
  },
});
