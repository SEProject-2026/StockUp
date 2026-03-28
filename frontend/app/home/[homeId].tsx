import React, { useCallback, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, RefreshControl } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";

// Components
import QuickActionButton from "@/src/components/ui/buttons/QuickActionButton";
import LocationAreaButton from "@/src/components/homes/LocationAreaButton";
import BottomNavBar from "@/src/layout/BottomNavBar";
import InventoryStatusCard from "@/src/components/homes/InventoryStatusCard";
import SideTitleCard from "@/src/components/ui/cards/SideTitleCard";
import ExpiringSoonCard from "@/src/components/homes/ExpiringSoonCard";

// Hooks & Logic
import { useHomeData } from "@/src/hooks/home/useHomeData";
import { useMembershipGuard } from "@/src/hooks/home/useMembershipGuard";
import { useShoppingList } from "@/src/hooks/shopping/useShoppingList";
import { setSelectedHomeId } from "@/src/utils/selected-home";
import { useRealtimeHomesRefresh } from "@/src/hooks/realtime/useRealtimeRefresh";

const BRAND_BLUE_SOFT = "#F0FAFF";

export default function HomeDashboardScreen() {
  const { homeId } = useLocalSearchParams<{ homeId: string }>();
  const currentHomeId = String(homeId);

  // הפעלת ההגנה: אם המשתמש יוסר מהבית הזה, הוא ייזרק החוצה אוטומטית
  useMembershipGuard(currentHomeId);

  const { stats, expiringSoon, loadData, isLoading } = useHomeData(currentHomeId);

  useEffect(() => {
    if (currentHomeId) {
      setSelectedHomeId(currentHomeId).catch(() => {});
    }
  }, [currentHomeId]);

  useEffect(() => {
    if (currentHomeId) {
      loadData();
    }
  }, [currentHomeId, loadData]);

  const onManualRefresh = useCallback(() => {
    loadData(true);
  }, [loadData]);

  const goInventory = (loc: string) => {
    router.push(`/inventory/${loc}?homeId=${currentHomeId}`);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.main}>
        <ScrollView
          contentContainerStyle={styles.container}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={isLoading && stats.total > 0} onRefresh={onManualRefresh} />
          }
        >
          {/* HEADER */}
          <View style={styles.headerRow}>
            <View style={styles.headerTextBlock}>
              <Text style={styles.appTitle}>StockUp</Text>
              <Text style={styles.appSubtitle}>ניהול מלאי הבית בצורה מסודרת ונקייה.</Text>
            </View>

            <View style={styles.headerIcon}>
              <Ionicons name="home-outline" size={22} color="#111827" />
            </View>
          </View>

          {isLoading && stats.total === 0 ? (
            <ActivityIndicator size="large" color="#007AFF" style={styles.loader} />
          ) : (
            <InventoryStatusCard stats={stats} />
          )}

          {/* HOME AREAS */}
          <View style={styles.horizontalSection}>
            <ScrollView
              horizontal
              style={styles.rtlScroll}
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalListContent}
            >
              <SideTitleCard label={"אזורי\nהבית"} />

              <LocationAreaButton
                label="מקרר"
                value={stats.fridge}
                icon="snow-outline"
                onPress={() => goInventory("fridge")}
              />
              <LocationAreaButton
                label="מקפיא"
                value={stats.freezer}
                icon="cube-outline"
                onPress={() => goInventory("freezer")}
              />
              <LocationAreaButton
                label="מזווה"
                value={stats.pantry}
                icon="restaurant-outline"
                onPress={() => goInventory("pantry")}
              />
              <LocationAreaButton
                label="ציוד ניקוי"
                value={stats.cleaningSupplies}
                icon="water-outline"
                onPress={() => goInventory("cleaning")}
              />
              <LocationAreaButton
                label="אחר"
                value={stats.other}
                icon="ellipsis-horizontal-outline"
                onPress={() => goInventory("other")}
              />
            </ScrollView>
          </View>

          {/* QUICK ACTIONS */}
          <View style={styles.horizontalSection}>
            <ScrollView
              horizontal
              style={styles.rtlScroll}
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalListContent}
            >
              <SideTitleCard label={"פעולות\nמהירות"} />

              <QuickActionButton
                label="סריקת קבלה"
                icon="camera-outline"
                onPress={() => router.push({ pathname: "/receipts/upload", params: { homeId: currentHomeId } })}
              />
              <QuickActionButton
                label="הוספת מוצר"
                icon="add-circle-outline"
                onPress={() => router.push({ pathname: "/inventory/add-item", params: { homeId: currentHomeId } })}
              />

            </ScrollView>
          </View>

          <ExpiringSoonCard items={expiringSoon} />
        </ScrollView>

        <BottomNavBar activeTab="home" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F4F4F4",
  },
  main: {
    flex: 1,
  },
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 100,
    gap: 18,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
  },
  headerTextBlock: {
    flex: 1,
  },
  appTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
    textAlign: "right",
  },
  appSubtitle: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "right",
    marginTop: 4,
  },
  headerIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#F0FAFF",
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },
  loader: {
    marginVertical: 40,
  },
  horizontalSection: {
    width: "100%",
  },
  rtlScroll: {
    direction: "rtl",
  },
  horizontalListContent: {
    flexDirection: "row",
    paddingHorizontal: 16,
    gap: 12,
    alignItems: "center",
  },
});