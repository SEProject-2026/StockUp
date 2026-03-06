import React, { useCallback, useEffect, useRef } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams, useFocusEffect } from "expo-router";

// Components
import QuickActionButton from "@/src/components/ui/buttons/QuickActionButton";
import LocationAreaButton from "@/src/components/homes/LocationAreaButton";
import BottomNavBar from "@/src/layout/BottomNavBar";
import InventoryStatusCard from "@/src/components/homes/InventoryStatusCard";
import SideTitleCard from "@/src/components/ui/cards/SideTitleCard";
import ExpiringSoonCard from "@/src/components/homes/ExpiringSoonCard";

// Hooks & Logic
import { useHomeData } from "@/src/hooks/useHomeData";
import { setSelectedHomeId } from "@/src/utils/selected-home";

const BRAND_BLUE_SOFT = "#F0FAFF";

export default function HomeDashboardScreen() {
  const { homeId } = useLocalSearchParams<{ homeId: string }>();
  const currentHomeId = String(homeId);

  const { stats, expiringSoon, loadData, isLoading } = useHomeData(currentHomeId);

  const homeAreasScrollRef = useRef<ScrollView>(null);
  const didAutoScrollAreas = useRef(false);

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
        <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
          
          {/* HEADER */}
          <View style={styles.headerRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.appTitle}>StockUp</Text>
              <Text style={styles.appSubtitle}>ניהול מלאי הבית בצורה מסודרת ונקייה.</Text>
            </View>
            <View style={styles.headerIcon}>
              <Ionicons name="home-outline" size={22} color="#111827" />
            </View>
          </View>

          {/* LOADING INDICATOR */}
          {isLoading ? (
            <ActivityIndicator size="large" color="#007AFF" style={{ marginVertical: 20 }} />
          ) : (
            <InventoryStatusCard stats={stats} />
          )}

          {/* HOME AREAS */}
          <View style={styles.horizontalSection}>
            <ScrollView
              ref={homeAreasScrollRef}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalListContent}
              onContentSizeChange={() => {
                if (didAutoScrollAreas.current) return;
                didAutoScrollAreas.current = true;
                requestAnimationFrame(() => {
                  homeAreasScrollRef.current?.scrollToEnd({ animated: false });
                });
              }}
            >
              <SideTitleCard label={"אזורי\nהבית"} />
              <LocationAreaButton label="מקרר" value={stats.fridge} icon="snow-outline" onPress={() => goInventory("fridge")} />
              <LocationAreaButton label="מקפיא" value={stats.freezer} icon="cube-outline" onPress={() => goInventory("freezer")} />
              <LocationAreaButton label="מזווה" value={stats.pantry} icon="restaurant-outline" onPress={() => goInventory("pantry")} />
              <LocationAreaButton label="ציוד ניקוי" value={stats.cleaningSupplies} icon="water-outline" onPress={() => goInventory("cleaning")} />
              <LocationAreaButton label="אחר" value={stats.other} icon="ellipsis-horizontal-outline" onPress={() => goInventory("other")} />
            </ScrollView>
          </View>

          {/* QUICK ACTIONS */}
          <View style={styles.horizontalSection}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.horizontalListContent}>
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
  safeArea: { flex: 1, backgroundColor: "#F4F4F4" },
  main: { flex: 1 },
  container: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 24, gap: 18 },
  headerRow: { flexDirection: "row-reverse", alignItems: "center" },
  appTitle: { fontSize: 22, fontWeight: "700", color: "#111827", textAlign: "right" },
  appSubtitle: { fontSize: 12, color: "#6B7280", textAlign: "right", marginTop: 4 },
  headerIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },
  horizontalSection: { flexDirection: "row-reverse", alignItems: "flex-start" },
  horizontalListContent: { flexDirection: "row-reverse", paddingRight: 4, paddingLeft: 4 },
});