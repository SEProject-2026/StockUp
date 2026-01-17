import React, { useMemo } from "react";
import { View, Text, StyleSheet, Pressable, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BRAND, LOCATION_LABEL, needsAttention, hasWeight, formatWeightKg } from "./review.shared";
import type { DetectedItem, LocationKey } from "./review.shared";

const SHADOW = Platform.select({
  ios: { shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 12, shadowOffset: { width: 0, height: 7 } },
  android: { elevation: 2 },
  default: {},
});

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

  const isWeighted = hasWeight(item);
  const kgText = isWeighted ? formatWeightKg(item.weight) : null;

  const attention = needsAttention(item);

  // ✅ ההצעה לשקילים מגיעה מ-quantity (לפי מה שאמרת)
  const suggestedFromQty =
    isWeighted && Number.isFinite(item.quantity) && item.quantity > 0 ? Math.round(item.quantity) : null;

  // badge ימני עליון:
  const rightBadgeText = isWeighted ? "מוצר שקיל" : `${item.quantity}${item.unit ? ` ${item.unit}` : ""}`;

  return (
    <Pressable onPress={onPress} style={[styles.card, attention && styles.cardAttention]}>
      <View style={[styles.accentBar, { backgroundColor: attention ? "#EF4444" : t.bar }]} />

      <View style={styles.content}>
        <View style={styles.topRow}>
          <Text style={styles.title} numberOfLines={1}>
            {item.name}
          </Text>

          <View style={[styles.qtyBadge, attention && styles.qtyBadgeAttention]}>
            <Text style={[styles.qtyText, attention && styles.qtyTextAttention]}>{rightBadgeText}</Text>
          </View>
        </View>

        {isWeighted && (
          <View style={styles.weightRow}>
            <Text style={styles.weightText}>זוהה {kgText} ק״ג</Text>

            <View style={{ flex: 1 }} />

            <View style={[styles.unitsBadge, attention && styles.unitsBadgeAttention]}>
              <Text style={[styles.unitsText, attention && styles.unitsTextAttention]}>
                {item.units_count && item.units_count > 0
                  ? `יח׳: ${item.units_count}`
                  : suggestedFromQty
                  ? `הצעה: ${suggestedFromQty}`
                  : "חסרות יחידות"}
              </Text>
            </View>
          </View>
        )}

        <View style={styles.bottomRow}>
          <LocationPill loc={item.location ?? "other"} />
          <View style={{ flex: 1 }} />

          {attention ? <Text style={styles.hintAttention}>צריך להשלים פרטים</Text> : <Text style={styles.hint}>לחץ לעריכה</Text>}
        </View>
      </View>

      <View style={[styles.chev, attention && styles.chevAttention]}>
        <Ionicons name="chevron-back" size={18} color={attention ? "#991B1B" : BRAND.MUTED} />
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

  cardAttention: {
    borderColor: "#FCA5A5",
    backgroundColor: "#FEF2F2",
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
  qtyBadgeAttention: { backgroundColor: "#FEE2E2", borderColor: "#FCA5A5" },
  qtyText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },
  qtyTextAttention: { color: "#991B1B" },

  weightRow: {
    marginTop: 8,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
  },
  weightText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },

  unitsBadge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
    backgroundColor: "#F3F4F6",
    borderColor: "#E5E7EB",
  },
  unitsBadgeAttention: { backgroundColor: "#FEE2E2", borderColor: "#FCA5A5" },
  unitsText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },
  unitsTextAttention: { color: "#991B1B" },

  bottomRow: { marginTop: 10, flexDirection: "row-reverse", alignItems: "center", gap: 8 },

  locPill: { paddingVertical: 4, paddingHorizontal: 10, borderRadius: 999, borderWidth: 1 },
  locPillText: { fontSize: 12, fontWeight: "800", color: BRAND.TEXT, textAlign: "right" },

  hint: { fontSize: 12, fontWeight: "700", color: BRAND.MUTED, textAlign: "right" },
  hintAttention: { fontSize: 12, fontWeight: "900", color: "#B91C1C", textAlign: "right" },

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
  chevAttention: { backgroundColor: "#FEE2E2", borderColor: "#FCA5A5" },
});
