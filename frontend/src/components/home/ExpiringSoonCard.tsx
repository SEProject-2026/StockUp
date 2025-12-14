import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { InventoryItem } from "../../context/inventory-context";
import HomeItemRow from "./HomeItemRow";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_RED = "#c43131ff";

type Props = {
  items: InventoryItem[];
};

export default function ExpiringSoonCard({ items }: Props) {
  return (
    <View style={styles.card}>
      <View className="header" style={styles.cardHeaderRow}>
        <View>
          <Text style={styles.cardTitle}>תוקף קרוב</Text>
          <Text style={styles.cardSubtitle}>
            מוצרים שעומדים לפוג בקרוב – כדי שלא יתבזבזו.
          </Text>
        </View>
        <View style={styles.badge}>
          <Ionicons name="time-outline" size={14} color={BRAND_RED} />
          <Text style={styles.badgeText}>עד 3 ימים</Text>
        </View>
      </View>

      {items.length === 0 ? (
        <Text style={styles.emptyText}>
          אין כרגע מוצרים עם תאריך תוקף קרוב. כל הכבוד על הניהול 🙂
        </Text>
      ) : (
        items.map((item) => (
          <HomeItemRow key={item.id} item={item} variant="warning" />
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 22,
    backgroundColor: "#FFFFFF",
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 2,
    gap: 10,
  },
  cardHeaderRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111827",
    textAlign: "right",
  },
  cardSubtitle: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "right",
    marginTop: 4,
  },
  badge: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: BRAND_BLUE_SOFT,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: "600",
    color: BRAND_RED,
  },
  emptyText: {
    fontSize: 12,
    color: "#6B7280",
    textAlign: "right",
  },
});
