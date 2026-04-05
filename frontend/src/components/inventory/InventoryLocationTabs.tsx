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
            style={{ borderStyle: "dashed" }}
          />
        )}

        <LocationChip
          label="עוד"
          icon="chevron-down"
          active={false}
          onPress={props.onOpenMore}
          style={{ marginRight: 6 }}
        />
      </ScrollView>

      <Text style={styles.selectedHint}>
        נבחר: <Text style={styles.selectedHintStrong}>{selected.label}</Text>
      </Text>
    </View>
  );
}

function LocationChip({
  label,
  icon,
  active,
  onPress,
  style,
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  active: boolean;
  onPress: () => void;
  style?: any;
}) {
  return (
    <TouchableOpacity onPress={onPress} style={[styles.catChip, active && styles.catChipActive, style]} activeOpacity={0.85}>
      <Ionicons name={icon} size={16} color={active ? "#FFFFFF" : COLORS.BRAND_MUTED} />
      <Text style={[styles.catChipText, active && styles.catChipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  locationContainer: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  locationChipsRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingVertical: 4,
  },
  catChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    backgroundColor: COLORS.BRAND_BLUE_SOFT,
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
  },
  catChipActive: { backgroundColor: COLORS.ACCENT, borderColor: COLORS.ACCENT },
  catChipText: { fontSize: 12, color: COLORS.BRAND_MUTED, fontWeight: "600" },
  catChipTextActive: { color: "#FFFFFF" },

  selectedHint: { marginTop: 6, textAlign: "right", fontSize: 12, color: COLORS.BRAND_MUTED },
  selectedHintStrong: { color: COLORS.BRAND_TEXT, fontWeight: "800" },
});
