import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { locationIcon } from "@/src/hooks/useBaseMode";

const BRAND = {
  PRIMARY: "#0284C7", PRIMARY_SOFT: "#E5F3FF", TEXT: "#111827", 
  MUTED: "#6B7280", BORDER: "#E5E7EB", SUCCESS: "#16A34A", 
  DANGER: "#DC2626", NOTE_LINE: "#E8EDF5", CARD: "#FFFFFF"
};

export const SummaryCard = ({ title, value, icon }: any) => (
  <View style={styles.summaryCard}>
    <View style={styles.summaryIconWrap}>
      <Ionicons name={icon} size={17} color={BRAND.PRIMARY} />
    </View>
    <View style={{ flex: 1 }}>
      <Text style={styles.summaryTitle}>{title}</Text>
      <Text style={styles.summaryValue}>{value}</Text>
    </View>
  </View>
);

export const ShoppingToggle = ({ enabled, onToggle }: any) => (
  <View style={styles.toggleCard}>
    <View style={styles.toggleTextWrap}>
      <Text style={styles.toggleTitle}>מצב קנייה</Text>
      <Text style={styles.toggleSubtitle}>כשהמצב דלוק אפשר לסמן פריטים שנאספו</Text>
    </View>
    <TouchableOpacity
      activeOpacity={0.9}
      onPress={onToggle}
      style={[styles.switchRoot, enabled && { backgroundColor: BRAND.PRIMARY }]}
    >
      <View style={[styles.switchThumb, enabled && { transform: [{ translateX: 20 }] }]} />
    </TouchableOpacity>
  </View>
);

export const SectionHeader = ({ title, location }: any) => (
  <View style={styles.sectionBlock}>
    <View style={styles.locationHeader}>
      <View style={styles.locationHeaderLine} />
      <View style={styles.locationHeaderChip}>
        <Ionicons name={(location === "UNSORTED" ? "albums-outline" : locationIcon(location)) as any} size={15} color={BRAND.PRIMARY} />
        <Text style={styles.locationHeaderText}>{title}</Text>
      </View>
    </View>
  </View>
);

export const NotebookRow = ({ item, mode, isPicked, onToggle, onIncrease, onDecrease, onRemove }: any) => {
  const qty = item.quantity || item.qty || item.targetQty || 1;
  return (
    <View style={[styles.noteRow, isPicked && { backgroundColor: "rgba(22,163,74,0.05)" }]}>
      <View style={styles.noteActions}>
        {mode === "SHOPPING" ? (
          <View style={styles.noteQtyPill}><Text style={styles.noteQtyText}>{qty}</Text></View>
        ) : (
          <>
            <TouchableOpacity onPress={onRemove} style={styles.noteIconBtn}><Ionicons name="trash-outline" size={16} color={BRAND.DANGER} /></TouchableOpacity>
            <TouchableOpacity onPress={onDecrease} style={styles.noteIconBtn}><Ionicons name="remove" size={16} color={BRAND.PRIMARY} /></TouchableOpacity>
            <View style={styles.noteQtyPill}><Text style={styles.noteQtyText}>{qty}</Text></View>
            <TouchableOpacity onPress={onIncrease} style={styles.noteIconBtn}><Ionicons name="add" size={16} color={BRAND.PRIMARY} /></TouchableOpacity>
          </>
        )}
      </View>
      <View style={styles.noteTextWrap}>
        <View style={styles.noteTitleRow}>
          {mode === "SHOPPING" && (
            <TouchableOpacity onPress={onToggle} style={[styles.pickBtn, isPicked && { backgroundColor: BRAND.SUCCESS, borderColor: BRAND.SUCCESS }]}>
              <Ionicons name={isPicked ? "checkmark" : "ellipse-outline"} size={16} color={isPicked ? "#fff" : BRAND.PRIMARY} />
            </TouchableOpacity>
          )}
          <Text style={[styles.noteTitle, isPicked && { textDecorationLine: "line-through", color: "#6B7280" }]}>{item?.name ?? "ללא שם"}</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  summaryCard: { flex: 1, backgroundColor: BRAND.CARD, borderRadius: 16, borderWidth: 1, borderColor: BRAND.BORDER, padding: 11, flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  summaryIconWrap: { width: 34, height: 34, borderRadius: 11, backgroundColor: BRAND.PRIMARY_SOFT, alignItems: "center", justifyContent: "center" },
  summaryTitle: { color: BRAND.MUTED, fontWeight: "800", fontSize: 11, textAlign: "right" },
  summaryValue: { marginTop: 2, color: BRAND.TEXT, fontWeight: "900", fontSize: 16, textAlign: "right" },
  toggleCard: { backgroundColor: "rgba(255,255,255,0.92)", borderWidth: 1, borderColor: BRAND.BORDER, borderRadius: 16, padding: 14, marginBottom: 12, flexDirection: "row-reverse", alignItems: "center", justifyContent: "space-between" },
  toggleTextWrap: { flex: 1, alignItems: "flex-end" },
  toggleTitle: { color: BRAND.TEXT, fontWeight: "900", fontSize: 14 },
  toggleSubtitle: { color: BRAND.MUTED, fontWeight: "700", fontSize: 11.5 },
  switchRoot: { width: 54, height: 32, borderRadius: 999, backgroundColor: "#D1D5DB", justifyContent: "center", paddingHorizontal: 4 },
  switchThumb: { width: 24, height: 24, borderRadius: 999, backgroundColor: "#FFFFFF" },
  sectionBlock: { marginBottom: 8 },
  locationHeader: { position: "relative", justifyContent: "center" },
  locationHeaderLine: { height: 1, backgroundColor: "#DCE4EF", width: "100%" },
  locationHeaderChip: { position: "absolute", alignSelf: "flex-end", flexDirection: "row-reverse", alignItems: "center", gap: 6, backgroundColor: "#F4F4F4", paddingHorizontal: 10, height: 26, borderRadius: 999 },
  locationHeaderText: { color: BRAND.TEXT, fontWeight: "900", fontSize: 13 },
  noteRow: { minHeight: 56, paddingHorizontal: 14, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  noteActions: { flexDirection: "row", alignItems: "center", gap: 6 },
  noteIconBtn: { width: 28, height: 28, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: "#F7FAFD", borderWidth: 1, borderColor: "#E7EDF5" },
  noteQtyPill: { minWidth: 30, height: 28, paddingHorizontal: 8, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: "#F7FAFD", borderWidth: 1, borderColor: "#E7EDF5" },
  noteQtyText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },
  noteTextWrap: { flex: 1, alignItems: "flex-end", marginLeft: 12 },
  noteTitleRow: { flexDirection: "row-reverse", alignItems: "center", gap: 8 },
  noteTitle: { fontSize: 14, fontWeight: "800", color: BRAND.TEXT },
  pickBtn: { width: 30, height: 30, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: "#F7FAFD", borderWidth: 1, borderColor: "#D7E7F7" },
});