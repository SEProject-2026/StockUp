// src/features/inventory/components/InventorylocationTabs.tsx
import React, { useMemo } from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { locationKey } from "@/src/components/inventory/inventory.utils";
import { CATEGORIES, QUICK_KEYS, COLORS } from "./filters.constants";

export default function InventorylocationTabs(props: {
  selectedTab: locationKey;
  onChangeTab: (tab: locationKey) => void;
  onOpenMore: () => void;
}) {
  const selected = useMemo(
    () => CATEGORIES.find((c) => c.key === props.selectedTab) ?? CATEGORIES[0],
    [props.selectedTab]
  );

  const quickCats = useMemo(() => CATEGORIES.filter((c) => QUICK_KEYS.includes(c.key)), []);
  const selectedIsExtra = !QUICK_KEYS.includes(props.selectedTab);
  const selectedExtra = selectedIsExtra ? selected : null;

  return (
    <View style={styles.locationContainer}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.locationChipsRow}>
        {quickCats.map((c) => (
          <LocationChip
            key={c.key}
            label={c.label}
            icon={c.icon}
            active={props.selectedTab === c.key}
            onPress={() => props.onChangeTab(c.key)}
          />
        ))}

        {selectedExtra && (
          <LocationChip
            key={`selected-extra-${selectedExtra.key}`}
            label={selectedExtra.label}
            icon={selectedExtra.icon}
            active
            onPress={props.onOpenMore}
          />
        )}

        <LocationChip
          label="עוד"
          icon="chevron-down"
          active={false}
          onPress={props.onOpenMore}
          isMore
        />
      </ScrollView>
    </View>
  );
}

function LocationChip({
  label,
  icon,
  active,
  onPress,
  isMore,
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  active: boolean;
  onPress: () => void;
  isMore?: boolean;
}) {
  return (
    <TouchableOpacity 
      onPress={onPress} 
      style={[
        styles.catChip, 
        active && styles.catChipActive,
        isMore && { backgroundColor: "transparent", borderWidth: 0 }
      ]} 
      activeOpacity={0.7}
    >
      <View style={[styles.iconCircle, active && styles.iconCircleActive]}>
        <Ionicons name={icon} size={15} color={active ? "#FFFFFF" : COLORS.BRAND_MUTED} />
      </View>
      <Text style={[styles.catChipText, active && styles.catChipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  locationContainer: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8 },
  locationChipsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 4,
  },
  catChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: "#FFFFFF",
    borderRadius: 999,
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    // Soft shadow
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  catChipActive: { 
    backgroundColor: COLORS.ACCENT, 
    borderColor: COLORS.ACCENT,
    shadowColor: COLORS.ACCENT,
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  iconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.BG_DIM,
    alignItems: "center",
    justifyContent: "center",
  },
  iconCircleActive: {
    backgroundColor: "rgba(255,255,255,0.25)",
  },
  catChipText: { fontSize: 13, color: COLORS.BRAND_MUTED, fontWeight: "700" },
  catChipTextActive: { color: "#FFFFFF" },
});
