// app/home/[homeId].tsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { View, Text, StyleSheet, ScrollView, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams, useFocusEffect } from "expo-router";

import QuickActionButton from "@/src/ui/QuickActionButton";
import CategoryAreaButton from "@/src/components/homes/CategoryAreaButton";
import BottomNavBar from "@/src/layout/BottomNavBar";
import InventoryStatusCard, { Stats } from "@/src/components/homes/InventoryStatusCard";
import SideTitleCard from "@/src/ui/SideTitleCard";
import ExpiringSoonCard from "@/src/components/homes/ExpiringSoonCard";

import { getAllStock, type ProductDTO } from "@/src/api/stock";
import type { Category } from "@/src/context/inventory-context";

const BRAND_BLUE_SOFT = "#F0FAFF";

type HomeItem = {
  id: string;
  name: string;
  category: Category;
  quantity: number;
  expiresAt?: string;
};

function locationToCategory(location?: string | null): Category {
  switch ((location ?? "").toUpperCase()) {
    case "FRIDGE":
      return "fridge";
    case "FREEZER":
      return "freezer";
    case "PANTRY":
      return "pantry";
    case "CLEANING_SUPPLIES":
      return "cleaning supplies";
    case "OTHER":
      return "other";
    default:
      return "other";
  }
}

function productDtoToHomeItems(dto: ProductDTO): HomeItem[] {
  const displayName = dto.nickname?.trim() ? dto.nickname : dto.original_name;
  const category = locationToCategory(dto.location);

  if (dto.items?.length) {
    return dto.items.map((it) => ({
      id: `${dto.id}__${it.expiration_date ?? "none"}`,
      name: displayName,
      category,
      quantity: it.quantity,
      expiresAt: it.expiration_date ?? undefined,
    }));
  }

  return [
    {
      id: `${dto.id}__none`,
      name: displayName,
      category,
      quantity: dto.quantity ?? 0,
      expiresAt: undefined,
    },
  ];
}

export default function HomeDashboardScreen() {
  const { homeId } = useLocalSearchParams<{ homeId: string }>();
  const currentHomeId = String(homeId);

  const [homeItems, setHomeItems] = useState<HomeItem[]>([]);
  const homeAreasScrollRef = useRef<ScrollView>(null);
  const didAutoScrollAreas = useRef(false);

  const loadHome = useCallback(async () => {
    if (!currentHomeId) return;

    try {
      const res = await getAllStock(currentHomeId);
      const products = res.data ?? [];
      setHomeItems(products.flatMap(productDtoToHomeItems));
    } catch (e: any) {
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לטעון נתוני בית");
      setHomeItems([]);
    }
  }, [currentHomeId]);

  useEffect(() => {
    loadHome();
  }, [loadHome]);

  useFocusEffect(
    useCallback(() => {
      loadHome();
    }, [loadHome])
  );

  const stats: Stats = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let fridge = 0,
      freezer = 0,
      pantry = 0,
      cleaningSupplies = 0,
      other = 0,
      expiringSoon = 0;

    homeItems.forEach((item) => {
      if (item.category === "fridge") fridge++;
      if (item.category === "freezer") freezer++;
      if (item.category === "pantry") pantry++;
      if (item.category === "cleaning supplies") cleaningSupplies++;
      if (item.category === "other") other++;

      if (item.expiresAt) {
        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffDays = (exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
        if (diffDays >= 0 && diffDays <= 3) expiringSoon++;
      }
    });

    return { total: homeItems.length, fridge, freezer, pantry, cleaningSupplies, other, expiringSoon };
  }, [homeItems]);

  const expiringSoonItems = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return homeItems
      .filter((item) => {
        if (!item.expiresAt) return false;
        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffDays = (exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
        return diffDays >= 0 && diffDays <= 3;
      })
      .sort((a, b) => new Date(a.expiresAt!).getTime() - new Date(b.expiresAt!).getTime())
      .slice(0, 3);
  }, [homeItems]);

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

          <InventoryStatusCard stats={stats} />

          {/* home areas */}
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

              <CategoryAreaButton
                label="מקרר"
                value={stats.fridge}
                icon="snow-outline"
                onPress={() =>
                  router.push({
                    pathname: "/inventory/[category]",
                    params: { category: "fridge", homeId: currentHomeId },
                  })
                }
              />

              <CategoryAreaButton
                label="מקפיא"
                value={stats.freezer}
                icon="cube-outline"
                onPress={() =>
                  router.push({
                    pathname: "/inventory/[category]",
                    params: { category: "freezer", homeId: currentHomeId },
                  })
                }
              />

              <CategoryAreaButton
                label="מזווה"
                value={stats.pantry}
                icon="restaurant-outline"
                onPress={() =>
                  router.push({
                    pathname: "/inventory/[category]",
                    params: { category: "pantry", homeId: currentHomeId },
                  })
                }
              />

              <CategoryAreaButton
                label="ציוד ניקוי"
                value={stats.cleaningSupplies}
                icon="water-outline"
                onPress={() =>
                  router.push({
                    pathname: "/inventory/[category]",
                    params: { category: "cleaning-supplies", homeId: currentHomeId },
                  })
                }
              />

              <CategoryAreaButton
                label="אחר"
                value={stats.other}
                icon="ellipsis-horizontal-outline"
                onPress={() =>
                  router.push({
                    pathname: "/inventory/[category]",
                    params: { category: "other", homeId: currentHomeId },
                  })
                }
              />
            </ScrollView>

          </View>

          {/* quick actions */}
          <View style={styles.horizontalSection}>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalListContent}
              contentOffset={{ x: 20, y: 0 }}
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

          <ExpiringSoonCard items={expiringSoonItems as any} />
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
