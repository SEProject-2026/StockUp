// frontend/app/components/HomeItemRow.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { InventoryItem } from "../inventory-store";

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

  return (
    <View
      style={[
        styles.row,
        variant === "warning" && styles.rowWarning,
      ]}
    >
      <View style={styles.leftStrip} />
      <View style={styles.main}>
        <View style={styles.headerRow}>
          <Text style={styles.name}>{item.name}</Text>
          <View style={styles.qtyChip}>
            <Text style={styles.qtyText}>x{item.quantity}</Text>
          </View>
        </View>
        <View style={styles.metaRow}>
          <Text style={styles.metaText}>
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
    flexDirection: "row",
    borderRadius: 16,
    overflow: "hidden",
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E8DED2",
    marginTop: 4,
  },
  rowWarning: {
    borderColor: "#DC2626",
    backgroundColor: "#FEE2E2",
  },
  leftStrip: {
    width: 4,
    backgroundColor: "#DC2626",
  },
  main: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  headerRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
  },
  name: {
    fontSize: 13,
    fontWeight: "600",
    color: "#3B2F28",
    textAlign: "right",
  },
  qtyChip: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: "#3B2F28",
  },
  qtyText: {
    fontSize: 11,
    color: "#FEFCE8",
  },
  metaRow: {
    flexDirection: "row-reverse",
    marginTop: 4,
  },
  metaText: {
    fontSize: 11,
    color: "#7C6A5A",
    textAlign: "right",
  },
});
