// src/features/inventory/components/InventoryStatusChips.tsx
import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { COLORS, type StatusFilter } from "./filters.constants";

export default function InventoryStatusChips(props: {
  value: StatusFilter;
  onChange: (v: StatusFilter) => void;
}) {
  return (
    <View style={styles.filterRow}>
      <View style={styles.filtersLeft}>
        <FilterChip label="הכול" active={props.value === "all"} onPress={() => props.onChange("all")} />
        <FilterChip
          label="תוקף קרוב"
          active={props.value === "soon"}
          onPress={() => props.onChange("soon")}
          style={{ marginLeft: 8 }}
        />
        <FilterChip
          label="פג תוקף"
          active={props.value === "expired"}
          onPress={() => props.onChange("expired")}
          style={{ marginLeft: 8 }}
        />
      </View>

      <Text style={styles.sortLabel}>מיון לפי מוצר</Text>
    </View>
  );
}

function FilterChip({
  label,
  active,
  onPress,
  style,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  style?: any;
}) {
  return (
    <TouchableOpacity onPress={onPress} style={[styles.filterChip, active && styles.filterChipActive, style]} activeOpacity={0.85}>
      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  filterRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    marginTop: 6,
    marginBottom: 4,
  },
  filtersLeft: { flexDirection: "row-reverse", alignItems: "center" },
  sortLabel: { fontSize: 13, color: COLORS.BRAND_MUTED, fontWeight: "600", textAlign: "right" },

  filterChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: COLORS.BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
  },
  filterChipActive: { backgroundColor: COLORS.ACCENT, borderColor: COLORS.ACCENT },
  filterChipText: { fontSize: 12, color: COLORS.BRAND_MUTED },
  filterChipTextActive: { color: "#FFFFFF", fontWeight: "600" },
});
