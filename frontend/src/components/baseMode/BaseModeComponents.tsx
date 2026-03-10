import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { locationIcon } from "@/src/hooks/useBaseMode";

const BRAND = {
  CARD: "#FFFFFF", BORDER: "#E5E7EB", TEXT: "#111827", MUTED: "#6B7280",
  PRIMARY: "#0284C7", PRIMARY_SOFT: "#E5F3FF", DANGER: "#DC2626",
  NOTE_LINE: "#E8EDF5", NOTE_MARGIN: "#D8E6F8", BG: "#F4F4F4",
};

export function SummaryCard({ title, value, icon }: { title: string; value: string; icon: any }) {
  return (
    <View style={styles.summaryCard}>
      <View style={styles.summaryIconWrap}><Ionicons name={icon} size={17} color={BRAND.PRIMARY} /></View>
      <View style={{ flex: 1 }}>
        <Text style={styles.summaryTitle}>{title}</Text>
        <Text style={styles.summaryValue}>{value}</Text>
      </View>
    </View>
  );
}

export function NotebookRow({ item, busy, onIncrease, onDecrease, onRemove }: any) {
  return (
    <View style={[styles.noteRow, busy && { opacity: 0.6 }]}>
      <View style={styles.noteActions}>
        <TouchableOpacity onPress={onRemove} disabled={busy} style={styles.noteIconBtn}>
          <Ionicons name="trash-outline" size={16} color={BRAND.DANGER} />
        </TouchableOpacity>
        <TouchableOpacity onPress={onDecrease} disabled={busy} style={styles.noteIconBtn}>
          <Ionicons name="remove" size={16} color={BRAND.PRIMARY} />
        </TouchableOpacity>
        <View style={styles.noteQtyPill}><Text style={styles.noteQtyText}>{item.targetQty}</Text></View>
        <TouchableOpacity onPress={onIncrease} disabled={busy} style={styles.noteIconBtn}>
          <Ionicons name="add" size={16} color={BRAND.PRIMARY} />
        </TouchableOpacity>
      </View>
      <View style={styles.noteTextWrap}>
        <Text style={styles.noteTitle}>{item.name}</Text>
        <Text style={styles.noteMeta}>{item.unit ?? "יח׳"}</Text>
      </View>
    </View>
  );
}

export function LocationSection({ section, busyIds, onIncrease, onDecrease, onRemove }: any) {
  if (section.items.length === 0) return null;
  return (
    <View style={styles.sectionBlock}>
      <View style={styles.locationHeader}>
        <View style={styles.locationHeaderLine} />
        <View style={styles.locationHeaderChip}>
          <Ionicons name={locationIcon(section.location) as any} size={15} color={BRAND.PRIMARY} />
          <Text style={styles.locationHeaderText}>{section.title}</Text>
        </View>
      </View>
      <View style={styles.notebookCard}>
        {section.items.map((item: any) => (
          <NotebookRow key={item.id} item={item} busy={busyIds.includes(item.id)}
            onIncrease={() => onIncrease(item.id)} onDecrease={() => onDecrease(item.id)} onRemove={() => onRemove(item.id)}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  summaryCard: { flex: 1, backgroundColor: BRAND.CARD, borderRadius: 16, borderWidth: 1, borderColor: BRAND.BORDER, padding: 11, flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  summaryIconWrap: { width: 34, height: 34, borderRadius: 11, backgroundColor: BRAND.PRIMARY_SOFT, alignItems: "center", justifyContent: "center" },
  summaryTitle: { color: BRAND.MUTED, fontWeight: "800", fontSize: 11, textAlign: "right" },
  summaryValue: { marginTop: 2, color: BRAND.TEXT, fontWeight: "900", fontSize: 16, textAlign: "right" },
  noteRow: { minHeight: 54, borderBottomWidth: 1, borderBottomColor: BRAND.NOTE_LINE, paddingRight: 14, paddingLeft: 48, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  noteActions: { flexDirection: "row", alignItems: "center", gap: 6 },
  noteIconBtn: { width: 28, height: 28, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: "#F7FAFD", borderWidth: 1, borderColor: "#E7EDF5" },
  noteQtyPill: { minWidth: 30, height: 28, paddingHorizontal: 8, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: "#F7FAFD", borderWidth: 1, borderColor: "#E7EDF5" },
  noteQtyText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT },
  noteTextWrap: { flex: 1, alignItems: "flex-end", marginLeft: 12 },
  noteTitle: { fontSize: 14, fontWeight: "800", color: BRAND.TEXT, textAlign: "right" },
  noteMeta: { marginTop: 2, fontSize: 11, color: BRAND.MUTED, fontWeight: "700", textAlign: "right" },
  sectionBlock: { marginBottom: 2 },
  locationHeader: { position: "relative", marginBottom: 8, justifyContent: "center" },
  locationHeaderLine: { height: 1, backgroundColor: "#DCE4EF", width: "100%" },
  locationHeaderChip: { position: "absolute", alignSelf: "flex-end", flexDirection: "row-reverse", alignItems: "center", gap: 6, backgroundColor: BRAND.BG, paddingHorizontal: 10, height: 26, borderRadius: 999 },
  locationHeaderText: { color: BRAND.TEXT, fontWeight: "900", fontSize: 13 },
  notebookCard: { backgroundColor: "rgba(255,255,255,0.97)", borderRadius: 18, borderWidth: 1, borderColor: "#E8ECF3", overflow: "hidden", paddingVertical: 2 },
});