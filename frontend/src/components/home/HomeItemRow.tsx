// frontend/app/components/HomeItemRow.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { InventoryItem } from "../../inventory/inventory-store";

const BRAND_YELLOW = "#3A6EA5";
const BRAND_PINK = "#c43131ff";

type Props = {
  item: InventoryItem;
  variant: "warning" | "neutral";
};

export default function HomeItemRow({ item, variant }: Props) {
  const categoryLabel =
    item.category === "fridge"
      ? "מקרר"
      : item.category === "freezer"
      ? "מקפיא"
      : "מזווה";

  const isWarning = variant === "warning";

  return (
    <View
      style={[
        styles.row,
        isWarning && styles.rowWarning,
      ]}
    >
      <View style={styles.main}>
        <View style={styles.headerRow}>
          <Text style={styles.name}>{item.name}</Text>
          <View style={styles.qtyChip}>
            <Text style={styles.qtyText}>x{item.quantity}</Text>
          </View>
        </View>
        <View style={styles.metaRow}>
          <Text
            style={[
              styles.metaText,
              isWarning && styles.metaTextWarning,
            ]}
          >
            {categoryLabel}
            {item.expiresAt ? " · תוקף " + item.expiresAt : ""}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    borderRadius: 22,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#F3F4F6",
    marginTop: 8,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 8,
    elevation: 2,
    overflow: "hidden",
  },
  rowWarning: {
    borderColor: BRAND_YELLOW,
  },
  main: {
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  headerRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
  },
  name: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
    textAlign: "right",
  },
  qtyChip: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: BRAND_PINK,
  },
  qtyText: {
    fontSize: 11,
    color: "#FFFFFF",
  },
  metaRow: {
    flexDirection: "row-reverse",
    marginTop: 4,
  },
  metaText: {
    fontSize: 11,
    color: "#6B7280",
    textAlign: "right",
  },
  metaTextWarning: {
    color: BRAND_PINK,
  },
});
