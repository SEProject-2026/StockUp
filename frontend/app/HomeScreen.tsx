//home screen
import React, { useMemo } from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useInventory } from "@/src/context/inventory-context";

import QuickActionButton from "@/src/ui/QuickActionButton";
import CategoryAreaButton from ".././src/components/home/CategoryAreaButton";
import BottomNavBar from "@/src/layout/BottomNavBar";
import InventoryStatusCard, {
  Stats,
} from "@/src/components/home/InventoryStatusCard";
import SideTitleCard from "@/src/ui/SideTitleCard";
import ExpiringSoonCard from "@/src/components/home/ExpiringSoonCard";

const BRAND_BLUE_SOFT = "#F0FAFF";

export default function HomeScreen() {
  const { items } = useInventory();

  const stats: Stats = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let fridge = 0;
    let freezer = 0;
    let pantry = 0;
    let expiringSoon = 0;

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

    return {
      total: items.length,
      fridge,
      freezer,
      pantry,
      expiringSoon,
    };
  }, [items]);

  const expiringSoonItems = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return items
      .filter((item) => {
        if (!item.expiresAt) return false;
        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffMs = exp.getTime() - today.getTime();
        const diffDays = diffMs / (1000 * 60 * 60 * 24);
        return diffDays >= 0 && diffDays <= 3;
      })
      .sort(
        (a, b) =>
          new Date(a.expiresAt!).getTime() - new Date(b.expiresAt!).getTime()
      )
      .slice(0, 3);
  }, [items]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.main}>
        <ScrollView
          contentContainerStyle={styles.container}
          showsVerticalScrollIndicator={false}
        >
          {/* HEADER */}
          <View style={styles.headerRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.appTitle}>StockUp</Text>
              <Text style={styles.appSubtitle}>
                ניהול מלאי הבית בצורה מסודרת ונקייה.
              </Text>
            </View>
            <View style={styles.headerIcon}>
              <Ionicons name="home-outline" size={22} color="#111827" />
            </View>
          </View>

          {/* inventory status */}
          <InventoryStatusCard stats={stats} />

          {/* home areas */}
          <View style={styles.horizontalSection}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalListContent}
              contentOffset={{ x: 150, y: 0 }}//padding to start from the right
            >
              <SideTitleCard label={"אזורי\nהבית"} />
              <CategoryAreaButton
                label="מקרר"
                value={stats.fridge}
                icon="snow-outline"
                onPress={() => router.push("/inventory/fridge")}
              />
              <CategoryAreaButton
                label="מקפיא"
                value={stats.freezer}
                icon="cube-outline"
                onPress={() => router.push("/inventory/freezer")}
              />
              <CategoryAreaButton
                label="מזווה"
                value={stats.pantry}
                icon="restaurant-outline"
                onPress={() => router.push("/inventory/pantry")}
              />
            </ScrollView>

          </View>

          {/* quick actions */}
          <View style={styles.horizontalSection}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalListContent}
              contentOffset={{ x: 20, y: 0 }}//padding to start from the right
            >
              <SideTitleCard label={"פעולות\nמהירות"} />
              <QuickActionButton
                label="סריקת קבלה"
                icon="camera-outline"
                onPress={() => { router.push("/receipts/upload");
                }}
              />
              <QuickActionButton
                label="הוספת מוצר"
                icon="add-circle-outline"
                onPress={() => router.push("./inventory/add-item")}
              />
            </ScrollView>
          </View>

          {/* expiring soon */}
          <ExpiringSoonCard items={expiringSoonItems} />
        </ScrollView>

        <BottomNavBar activeTab="home" />
      </View>
    </SafeAreaView>
  );
}

/* ---------- STYLES  ---------- */

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
    paddingBottom: 24,
    gap: 18,
  },

  /* HEADER */
  headerRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
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
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },

  horizontalSection: {
    flexDirection: "row-reverse",
    alignItems: "flex-start",
  },
  horizontalListContent: {
    flexDirection: "row-reverse",
    paddingRight: 4,
    paddingLeft: 4,
  },
});
