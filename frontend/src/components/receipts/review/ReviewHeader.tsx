import React from "react";
import { View, Text, StyleSheet, Pressable, TextInput, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BRAND } from "./review.shared";
import type { LocationKey } from "./review.shared";

const SHADOW = Platform.select({
  ios: {
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
  },
  android: { elevation: 2 },
  default: {},
});

function FilterChip(props: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  count?: number;
  active?: boolean;
  onPress?: () => void;
}) {
  const { icon, label, count, active, onPress } = props;

  const bg = active ? BRAND.BLUE_SOFT : BRAND.CARD;
  const border = active ? BRAND.BLUE_LINE : BRAND.BORDER;
  const iconColor = BRAND.TEXT;

  return (
    <Pressable onPress={onPress} style={[styles.chip, { backgroundColor: bg, borderColor: border }]}>
      <Ionicons name={icon} size={14} color={iconColor} />
      <Text style={styles.chipText}>{label}</Text>

      {typeof count === "number" ? (
        <View style={[styles.countPill, active && { backgroundColor: "#E6F0FF", borderColor: BRAND.BLUE_LINE }]}>
          <Text style={styles.countText}>{count}</Text>
        </View>
      ) : null}
    </Pressable>
  );
}

function statChip(icon: keyof typeof Ionicons.glyphMap, label: string) {
  return (
    <View style={[styles.chip, { backgroundColor: BRAND.BLUE_SOFT, borderColor: BRAND.BLUE_LINE }]}>
      <Ionicons name={icon} size={14} color={BRAND.TEXT} />
      <Text style={styles.chipText}>{label}</Text>
    </View>
  );
}

export default function ReviewHeader(props: {
  totalCount: number;
  filteredCount: number;
  query: string;
  onChangeQuery: (v: string) => void;
  locationCounts: Record<LocationKey, number>;
  onBack: () => void;
  onOpenAdd: () => void;

  activeLocation: LocationKey | "all";
  onChangeActiveLocation: (v: LocationKey | "all") => void;
}) {
  const {
    totalCount,
    filteredCount,
    query,
    onChangeQuery,
    locationCounts,
    onBack,
    onOpenAdd,
    activeLocation,
    onChangeActiveLocation,
  } = props;

  return (
    <View style={styles.headerWrap}>
      <View style={styles.headerTopRow}>
        <Pressable onPress={onBack} style={styles.headerIconBtn}>
          <Ionicons name="chevron-forward" size={20} color={BRAND.TEXT} />
        </Pressable>

        <View style={{ flex: 1 }}>
          <Text style={styles.title}>סקירת קבלה</Text>
          <Text style={styles.subtitle}>ערכו פריטים לפני הוספה למלאי</Text>
        </View>

        <Pressable onPress={onOpenAdd} style={styles.headerAddBtn}>
          <Ionicons name="add" size={18} color={BRAND.TEXT} />
          <Text style={styles.headerAddText}>הוסף</Text>
        </Pressable>
      </View>

      <View style={[styles.chipsRow, { marginTop: 8 }]}>
        <FilterChip
          icon="apps"
          label="הכל"
          count={totalCount}
          active={activeLocation === "all"}
          onPress={() => onChangeActiveLocation("all")}
        />
        <FilterChip
          icon="ellipsis-horizontal"
          label="אחר"
          count={locationCounts.other}
          active={activeLocation === "other"}
          onPress={() => onChangeActiveLocation(activeLocation === "other" ? "all" : "other")}
        />
        <FilterChip
          icon="snow-outline"
          label="מקרר"
          count={locationCounts.fridge}
          active={activeLocation === "fridge"}
          onPress={() => onChangeActiveLocation(activeLocation === "fridge" ? "all" : "fridge")}
        />
        <FilterChip
          icon="snow"
          label="מקפיא"
          count={locationCounts.freezer}
          active={activeLocation === "freezer"}
          onPress={() => onChangeActiveLocation(activeLocation === "freezer" ? "all" : "freezer")}
        />
        <FilterChip
          icon="cube-outline"
          label="מזווה"
          count={locationCounts.pantry}
          active={activeLocation === "pantry"}
          onPress={() => onChangeActiveLocation(activeLocation === "pantry" ? "all" : "pantry")}
        />
        <FilterChip
          icon="sparkles-outline"
          label="וטואלטיקה ניקיון"
          count={locationCounts.cleaning}
          active={activeLocation === "cleaning"}
          onPress={() => onChangeActiveLocation(activeLocation === "cleaning" ? "all" : "cleaning")}
        />

      </View>

      {/* ✅ חיפוש */}
      <View style={styles.searchWrap}>
        <Ionicons name="search-outline" size={18} color={BRAND.MUTED} />
        <TextInput
          value={query}
          onChangeText={onChangeQuery}
          placeholder="חיפוש מוצר…"
          placeholderTextColor="#9CA3AF"
          style={styles.searchInput}
          textAlign="right"
        />
        {query.trim() ? (
          <Pressable onPress={() => onChangeQuery("")} style={styles.searchClear}>
            <Ionicons name="close" size={16} color={BRAND.TEXT} />
          </Pressable>
        ) : (
          <View style={{ width: 28 }} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  headerWrap: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 12,
    backgroundColor: BRAND.BG,
  },
  headerTopRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  headerIconBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: BRAND.BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND.BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },
  headerAddBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: BRAND.CARD,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    ...SHADOW,
  },
  headerAddText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },

  title: { fontSize: 18, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },
  subtitle: { fontSize: 12, color: BRAND.MUTED, textAlign: "right", marginTop: 2 },

  chipsRow: {
    marginTop: 10,
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
  },

  chip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
  },
  chipText: { fontSize: 12, fontWeight: "800", color: BRAND.TEXT },

  countPill: {
    marginRight: 6,
    height: 20,
    paddingHorizontal: 8,
    borderRadius: 999,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
  },
  countText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },

  searchWrap: {
    marginTop: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    backgroundColor: BRAND.CARD,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    ...SHADOW,
  },
  searchInput: { flex: 1, fontSize: 14, color: BRAND.TEXT, paddingVertical: 0 },
  searchClear: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: BRAND.BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND.BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },
});
