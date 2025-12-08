import React, { useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useInventory } from "./inventory-store";
import { LinearGradient } from "expo-linear-gradient";

import QuickActionButton from "./components/QuickActionButton";
import CategoryAreaButton from "./components/CategoryAreaButton";
import HomeItemRow from "./components/HomeItemRow";

export default function HomeScreen() {
  const { items } = useInventory();

  const stats = useMemo(() => {
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

  const recentItems = useMemo(
    () =>
      [...items]
        .sort((a, b) => Number(b.id) - Number(a.id))
        .slice(0, 3),
    [items]
  );

  // צבע אחיד לאזורי מקרר / מקפיא / מזווה
  const areaBackground = "#E5E7EB";
  const areaIconColor = "#374151";

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        {/* כרטיס עליון */}
        <View style={styles.heroCard}>
          <LinearGradient
            colors={["#F9FAFB", "#F3F4F6"]}
            start={{ x: 1, y: 0 }}
            end={{ x: 0, y: 1 }}
            style={styles.heroGradient}
          >
            <View style={styles.heroHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.heroTitle}>מלאי הבית</Text>
                <Text style={styles.heroSubtitle}>
                  כל מה שיש במקרר, במקפיא ובמזווה – במסך אחד.
                </Text>
              </View>
              <View style={styles.heroAvatar}>
                <Ionicons name="home-outline" size={26} color="#E5E7EB" />
              </View>
            </View>

            <View style={styles.heroStatsRow}>
              <HeroStat
                label="סה״כ פריטים"
                value={stats.total}
                icon="cube-outline"
              />
              <HeroStat
                label="תוקף קרוב"
                value={stats.expiringSoon}
                icon="alert-circle-outline"
                accent
              />
            </View>

            <View style={styles.heroAreasRow}>
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
            </View>
          </LinearGradient>
        </View>

        {/* פעולות מהירות */}
        <View style={styles.quickActionsRow}>
          <QuickActionButton
            label="סריקת קבלה"
            icon="camera-outline"
            primary
            onPress={() => {
              // בהמשך: router.push("/scan")
            }}
          />
          <QuickActionButton
            label="הוספת מוצר"
            icon="add-circle-outline"
            onPress={() => router.push("/add-item")}
          />
          <QuickActionButton
            label="כל המלאי"
            icon="grid-outline"
            onPress={() => router.push("/inventory")}
          />
        </View>

        {/* תוקף קרוב */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeaderRow}>
            <View>
              <Text style={styles.sectionTitle}>תוקף קרוב</Text>
              <Text style={styles.sectionSubtitle}>
                מוצרים שכדאי לבדוק בימים הקרובים
              </Text>
            </View>
            <View style={styles.sectionBadge}>
              <Ionicons name="time-outline" size={14} color="#DC2626" />
              <Text style={styles.sectionBadgeText}>עד 3 ימים</Text>
            </View>
          </View>

          {expiringSoonItems.length === 0 ? (
            <Text style={styles.emptyText}>
              אין כרגע מוצרים עם תוקף קרוב. 
            </Text>
          ) : (
            expiringSoonItems.map((item) => (
              <HomeItemRow key={item.id} item={item} variant="warning" />
            ))
          )}
        </View>

        {/* נוספו לאחרונה */}
        <View style={styles.sectionCard}>
          <View style={styles.sectionHeaderRow}>
            <View>
              <Text style={styles.sectionTitle}>נוספו לאחרונה</Text>
              <Text style={styles.sectionSubtitle}>
                הצצה מהירה לפריטים שהזנת לאחרונה
              </Text>
            </View>
          </View>

          {recentItems.length === 0 ? (
            <Text style={styles.emptyText}>
              עדיין לא נוספו פריטים. התחילי בסריקה או הוספה ידנית.
            </Text>
          ) : (
            recentItems.map((item) => (
              <HomeItemRow key={item.id} item={item} variant="neutral" />
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

/* ---------- קומפוננטה קטנה שנשארת כאן ---------- */

function HeroStat({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: number;
  icon: keyof typeof Ionicons.glyphMap;
  accent?: boolean;
}) {
  return (
    <View style={[styles.heroStat, accent && styles.heroStatAccent]}>
      <View style={styles.heroStatIconCircle}>
        <Ionicons
          name={icon}
          size={16}
          color={accent ? "#DC2626" : "#4B5563"}
        />
      </View>
      <Text style={styles.heroStatValue}>{value}</Text>
      <Text style={styles.heroStatLabel}>{label}</Text>
    </View>
  );
}

/* ---------- STYLES ---------- */

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 32,
    gap: 16,
  },

  /* HERO */
  heroCard: {
    borderRadius: 24,
    padding: 18,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  heroGradient: {
    borderRadius: 24,
    padding: 18,
  },
  heroHeaderRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    marginBottom: 14,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    textAlign: "right",
  },
  heroSubtitle: {
    fontSize: 13,
    color: "#6B7280",
    textAlign: "right",
  },
  heroAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#111827",
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },
  heroStatsRow: {
    flexDirection: "row-reverse",
    gap: 10,
    marginBottom: 10,
  },
  heroStat: {
    flex: 1,
    borderColor: "#8e444463",
    borderWidth: 1,
    backgroundColor: "#F3F4F6",
    borderRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 10,
    alignItems: "flex-end",
    gap: 4,
  },
  heroStatAccent: {
    borderColor: "#8e444463",
    borderWidth: 1,
    backgroundColor: "#F3F4F6",
  },
  heroStatIconCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "flex-start",
  },
  heroStatValue: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
  },
  heroStatLabel: {
    fontSize: 11,
    color: "#6B7280",
  },

  heroAreasRow: {
    flexDirection: "row-reverse",
    gap: 6,
    marginTop: 2,
  },

  /* QUICK ACTIONS */
  quickActionsRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    gap: 8,
  },

  /* SECTIONS */
  sectionCard: {
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    padding: 14,
    gap: 8,
  },
  sectionHeaderRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111827",
  },
  sectionSubtitle: {
    fontSize: 11,
    color: "#6B7280",
    marginTop: 2,
    textAlign: "right",
  },
  sectionBadge: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: "#FEE2E2",
    borderWidth: 1,
    borderColor: "#FCA5A5",
  },
  sectionBadgeText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#B91C1C",
  },
  emptyText: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "right",
    marginTop: 4,
  },
});
