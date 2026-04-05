import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { CatalogItem } from "@/src/api/catalog";

export default function SuggestionsList(props: {
  items: CatalogItem[];
  onPick: (item: CatalogItem) => void;
  maxItems?: number;
}) {
  const max = props.maxItems ?? 8;
  const items = props.items.slice(0, max);

  if (!items.length) return null;

  return (
    <View style={styles.container}>
      {items.map((it, idx) => {
        const right = it.brand?.trim() ? it.brand.trim() : it.barcode ?? "";
        return (
          <TouchableOpacity
            key={`${it.barcode ?? it.name}-${idx}`}
            activeOpacity={0.85}
            onPress={() => props.onPick(it)}
            style={styles.row}
          >
            <View style={styles.right}>
              {right ? <Text style={styles.rightText}>{right}</Text> : null}
              <Ionicons name="chevron-back" size={16} color="#9CA3AF" />
            </View>

            <Text style={styles.name} numberOfLines={1}>
              {it.name}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 14,
    overflow: "hidden",
    backgroundColor: "#FFFFFF",
  },
  row: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  name: {
    flex: 1,
    fontSize: 13,
    fontWeight: "800",
    color: "#111827",
    textAlign: "right",
  },
  right: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
  },
  rightText: {
    fontSize: 12,
    color: "#6B7280",
    fontWeight: "700",
    textAlign: "right",
  },
});
