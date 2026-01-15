import React, { useMemo } from "react";
import { View, Text, StyleSheet, Pressable, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BRAND, LOCATION_LABEL } from "./review.shared";
import type { DetectedItem, LocationKey } from "./review.shared";

const SHADOW = Platform.select({
  ios: { shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 12, shadowOffset: { width: 0, height: 7 } },
  android: { elevation: 2 },
  default: {},
});

// ✅ צבע עדין לכל מיקום (לא צורח)
function locTone(loc: LocationKey) {
  switch (loc) {
    case "fridge":
      return { bar: "#f65a3b", soft: "#EAF2FF", line: "#CFE2FF" };
    case "freezer":
      return { bar: "#06B6D4", soft: "#E6FBFF", line: "#BEEAF2" }; 
    case "pantry":
      return { bar: "#F59E0B", soft: "#FFF4DE", line: "#FFE1A6" }; 
    case "cleaning":
      return { bar: "#8B5CF6", soft: "#F1E9FF", line: "#DCCBFF" }; 
    default:
      return { bar: "#64748B", soft: "#EEF2F7", line: "#D9E0EA" }; 
  }
}

function LocationPill({ loc }: { loc: LocationKey }) {
  const t = locTone(loc);
  return (
    <View style={[styles.locPill, { backgroundColor: t.soft, borderColor: t.line }]}>
      <Text style={styles.locPillText}>{LOCATION_LABEL[loc]}</Text>
    </View>
  );
}

export default function ReviewListItem(props: { item: DetectedItem; onPress: () => void }) {
  const { item, onPress } = props;

  const t = useMemo(() => locTone(item.location ?? "other"), [item.location]);
  const unitText = item.unit ? ` ${item.unit}` : "";
  const qtyText = `${item.quantity}${unitText}`;

  return (
    <Pressable onPress={onPress} style={styles.card}>
      <View style={[styles.accentBar, { backgroundColor: t.bar }]} />

      <View style={styles.content}>
        <View style={styles.topRow}>
          <Text style={styles.title} numberOfLines={1}>
            {item.name}
          </Text>

          <View style={styles.qtyBadge}>
            <Text style={styles.qtyText}>{qtyText}</Text>
          </View>
        </View>

        <View style={styles.bottomRow}>
          <LocationPill loc={item.location ?? "other"} />
          <View style={{ flex: 1 }} />
          <Text style={styles.hint}>לחץ לעריכה</Text>
        </View>
      </View>

      <View style={styles.chev}>
        <Ionicons name="chevron-back" size={18} color={BRAND.MUTED} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 12,
    ...SHADOW,
  },

  accentBar: {
    width: 5,
    alignSelf: "stretch",
    borderRadius: 999,
    opacity: 0.9,
  },

  content: { flex: 1 },

  topRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },

  title: { flex: 1, fontSize: 14, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },

  qtyBadge: {
    backgroundColor: BRAND.BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND.BLUE_LINE,
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
  },
  qtyText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },

  bottomRow: { marginTop: 10, flexDirection: "row-reverse", alignItems: "center", gap: 8 },

  locPill: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
  },
  locPillText: { fontSize: 12, fontWeight: "800", color: BRAND.TEXT, textAlign: "right" },

  hint: { fontSize: 12, fontWeight: "700", color: BRAND.MUTED, textAlign: "right" },

  chev: {
    width: 30,
    height: 30,
    borderRadius: 999,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
  },
});
