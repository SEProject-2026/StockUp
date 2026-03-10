import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";
const CARD = "#FFFFFF";
const BRAND_PRIMARY = "#0284C7";

export const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <View style={styles.section}>
    <Text style={styles.sectionTitle}>{title}</Text>
    <View style={styles.sectionCard}>{children}</View>
  </View>
);

export const SettingsRow = ({ icon, title, subtitle, right, onPress, danger }: any) => {
  const content = (
    <View style={styles.row}>
      <View style={[styles.rowIcon, danger && styles.rowIconDanger]}>
        <Ionicons name={icon} size={18} color={danger ? "#B91C1C" : BRAND_PRIMARY} />
      </View>
      <View style={styles.rowText}>
        <Text style={[styles.rowTitle, danger && { color: "#B91C1C" }]}>{title}</Text>
        {!!subtitle && <Text style={styles.rowSubtitle}>{subtitle}</Text>}
      </View>
      <View style={styles.rowRight}>
        {right ?? <Ionicons name="chevron-back" size={18} color={MUTED} />}
      </View>
    </View>
  );

  return onPress ? (
    <TouchableOpacity style={styles.rowWrap} onPress={onPress} activeOpacity={0.7}>{content}</TouchableOpacity>
  ) : (
    <View style={styles.rowWrap}>{content}</View>
  );
};

export const Divider = () => <View style={styles.divider} />;

const styles = StyleSheet.create({
  section: { gap: 8 },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "800",
    color: MUTED,
    textAlign: "right",
    paddingHorizontal: 2,
    letterSpacing: 0.5,
    textTransform: "uppercase",
  },
  sectionCard: {
    backgroundColor: CARD,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: BORDER,
    overflow: "hidden",
    // Shadows לפי העיצוב המקורי
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  rowWrap: { paddingHorizontal: 12, paddingVertical: 12 },
  row: { flexDirection: "row-reverse", alignItems: "center", gap: 12 },
  rowIcon: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: "rgba(2,132,199,0.10)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.14)",
  },
  rowIconDanger: {
    backgroundColor: "rgba(185,28,28,0.08)",
    borderColor: "rgba(185,28,28,0.18)",
  },
  rowText: { flex: 1, gap: 3 },
  rowTitle: { fontSize: 14, fontWeight: "900", color: TEXT, textAlign: "right" },
  rowSubtitle: { fontSize: 12, color: MUTED, textAlign: "right", lineHeight: 16 },
  rowRight: { alignItems: "center", justifyContent: "center" },
  divider: { height: 1, backgroundColor: BORDER, marginHorizontal: 12 },
});