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
      <View style={styles.filtersWrapper}>
        <FilterChip label="הכול" active={props.value === "all"} onPress={() => props.onChange("all")} />
        <FilterChip
          label="תוקף קרוב"
          active={props.value === "soon"}
          onPress={() => props.onChange("soon")}
        />
        <FilterChip
          label="פג תוקף"
          active={props.value === "expired"}
          onPress={() => props.onChange("expired")}
        />
      </View>
    </View>
  );
}

function FilterChip({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity 
      onPress={onPress} 
      style={[styles.filterChip, active && styles.filterChipActive]} 
      activeOpacity={0.7}
    >
      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  filterRow: {
    paddingHorizontal: 16,
    marginTop: 12,
    marginBottom: 8,
  },
  filtersWrapper: { 
    flexDirection: "row", 
    backgroundColor: COLORS.BG_DIM,
    borderRadius: 12,
    padding: 4,
    gap: 4,
  },
  filterChip: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
    borderRadius: 8,
  },
  filterChipActive: { 
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  filterChipText: { fontSize: 13, color: COLORS.BRAND_MUTED, fontWeight: "600" },
  filterChipTextActive: { color: COLORS.ACCENT, fontWeight: "800" },
});
