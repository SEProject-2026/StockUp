import React, { useCallback } from "react";
import { View, StyleSheet, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams, useFocusEffect } from "expo-router";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";

import { InventoryFiltersBar } from "@/src/components/inventory/InventoryFiltersBar";
import { GroupedInventoryList } from "@/src/components/inventory/GroupedInventoryList";
import { EditItemModal } from "@/src/components/inventory/EditItemModal";

import type { locationKey } from "@/src/components/inventory/inventory.utils";
import { useInventoryData } from "@/src/hooks/useInventoryData";
import { useRealtimeInventoryRefresh } from "@/src/hooks/useRealtimeInventoryRefresh";
import { useMembershipGuard } from "@/src/hooks/useMembershipGuard"; // <--- ייבוא ה-Hook

export function InventoryScreenBase({
  initiallocation = "all",
  title = "מלאי",
  hideTabs = false,
}: {
  initiallocation?: locationKey;
  title?: string;
  hideTabs?: boolean;
}) {
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const currentHomeId = homeId ? String(homeId) : undefined;

  // הפעלת ההגנה: זריקה מהמסך אם המשתמש הוסר מהבית
  useMembershipGuard(currentHomeId);

  const inv = useInventoryData({
    homeId: currentHomeId,
    initiallocation,
    hideTabs,
  });

  useRealtimeInventoryRefresh(currentHomeId, () => inv.loadInventory("soft"));

  useFocusEffect(
    useCallback(() => {
      if (!currentHomeId) return;
      void inv.loadInventory("soft");
    }, [currentHomeId, inv.loadInventory])
  );

  const handleBack = () => {
    if (currentHomeId) {
      router.replace({
        pathname: "/home/[homeId]",
        params: { homeId: currentHomeId },
      });
    } else {
      router.back();
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

      <View style={{ flex: 1 }}>
        <ScreenHeader title={title} onBack={handleBack} />

        {!currentHomeId ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#0284C7" />
          </View>
        ) : (
          <>
            <InventoryFiltersBar
              hideTabs={hideTabs}
              selectedTab={inv.selectedTab}
              onChangeTab={inv.setSelectedTab}
              search={inv.search}
              onChangeSearch={inv.setSearch}
              statusFilter={inv.statusFilter}
              onChangeStatusFilter={inv.setStatusFilter}
              filtersVisible={true}
            />

            {inv.initialLoading ? (
              <View style={styles.center}>
                <ActivityIndicator size="large" color="#0284C7" />
              </View>
            ) : (
              <>
                <GroupedInventoryList
                  groupedItems={inv.groupedItems}
                  searchQuery={inv.search}
                  onChangeQty={inv.changeQty}
                  onEditItem={(it: any) => inv.setItemToEdit(it)}
                  onDeleteItem={inv.deleteRow}
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
          </>
        )}
      </View>

    <EditItemModal
      visible={!!inv.itemToEdit}
      item={inv.itemToEdit}
      onClose={() => inv.setItemToEdit(null)}
      onSave={(values) => {
        if (inv.itemToEdit) {
          inv.saveEdit(inv.itemToEdit.itemId, values);
        }
      }}
    />
    </SafeAreaView>
  );
}

export default function InventoryScreen() {
  return <InventoryScreenBase initiallocation="all" title="מלאי" hideTabs={false} />;
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F4F4" },
  gradientBackground: { ...StyleSheet.absoluteFillObject },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
});