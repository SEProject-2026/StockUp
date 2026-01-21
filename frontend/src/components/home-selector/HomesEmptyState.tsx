import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND_PRIMARY = "#0284C7";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";

export default function HomesEmptyState({
  onCreate,
  onJoin,
}: {
  onCreate: () => void;
  onJoin: () => void;
}) {
  return (
    <View style={styles.empty}>
      <View style={styles.emptyIcon}>
        <Ionicons name="home" size={22} color={BRAND_PRIMARY} />
      </View>

      <Text style={styles.emptyTitle}>אין לך עדיין בתים</Text>
      <Text style={styles.emptySubtitle}>
        צור בית חדש או הצטרפי לבית קיים בעזרת קוד הזמנה.
      </Text>

      <View style={styles.row}>
        <TouchableOpacity onPress={onCreate} style={styles.primaryBtn} activeOpacity={0.9}>
          <Ionicons name="add" size={18} color="white" />
          <Text style={styles.primaryBtnText}>יצירת בית</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={onJoin} style={styles.secondaryBtn} activeOpacity={0.9}>
          <Ionicons name="key-outline" size={18} color={TEXT} />
          <Text style={styles.secondaryBtnText}>יש לי קוד</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  empty: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
    gap: 10,
  },
  emptyIcon: {
    width: 56,
    height: 56,
    borderRadius: 18,
    backgroundColor: "rgba(2,132,199,0.10)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.16)",
  },
  emptyTitle: { fontSize: 18, fontWeight: "900", color: TEXT },
  emptySubtitle: {
    fontSize: 13,
    color: MUTED,
    textAlign: "center",
    lineHeight: 18,
    marginBottom: 6,
  },
  row: { flexDirection: "row-reverse", gap: 10 },

  primaryBtn: {
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    minWidth: 140,
    justifyContent: "center",
  },
  primaryBtnText: { color: "white", fontWeight: "800", fontSize: 14 },

  secondaryBtn: {
    backgroundColor: "white",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: BORDER,
    minWidth: 120,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row-reverse",
    gap: 8,
  },
  secondaryBtnText: { color: TEXT, fontWeight: "800", fontSize: 14 },
});
