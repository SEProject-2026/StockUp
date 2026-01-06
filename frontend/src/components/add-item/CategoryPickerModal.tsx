import React from "react";
import { Modal, Pressable, View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { Category } from "./types";

const BRAND_PRIMARY = "#0284C7";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BORDER = "#E5E7EB";
const BRAND_BLUE_SOFT = "#F0FAFF";

export default function CategoryPickerModal(props: {
  open: boolean;
  selected: Category;
  options: Array<{ key: Category; label: string; icon: keyof typeof Ionicons.glyphMap }>;
  onClose: () => void;
  onSelect: (c: Category) => void;
}) {
  return (
    <Modal visible={props.open} animationType="fade" transparent onRequestClose={props.onClose}>
      <Pressable style={styles.backdrop} onPress={props.onClose} />
      <View style={styles.sheet}>
        <View style={styles.header}>
          <Text style={styles.title}>בחירת קטגוריה</Text>
          <TouchableOpacity onPress={props.onClose} activeOpacity={0.85}>
            <Ionicons name="close" size={20} color={BRAND_MUTED} />
          </TouchableOpacity>
        </View>

        {props.options.map((opt) => {
          const active = opt.key === props.selected;
          return (
            <TouchableOpacity
              key={opt.key}
              style={[styles.row, active && styles.rowActive]}
              onPress={() => props.onSelect(opt.key)}
              activeOpacity={0.85}
            >
              <View style={styles.rowInner}>
                <View style={styles.rowLabelWrap}>
                  <Text style={[styles.rowText, active && styles.rowTextActive]}>{opt.label}</Text>
                  {active && <Ionicons name="checkmark" size={18} color={BRAND_PRIMARY} />}
                </View>
                <Ionicons name={opt.icon} size={18} color={active ? BRAND_PRIMARY : BRAND_MUTED} />
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.25)" },
  sheet: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 18,
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    padding: 12,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  header: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: 8,
  },
  title: { fontSize: 14, fontWeight: "700", color: BRAND_TEXT, textAlign: "right" },
  row: { paddingVertical: 12, paddingHorizontal: 10, borderRadius: 12 },
  rowActive: { backgroundColor: BRAND_BLUE_SOFT },
  rowInner: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  rowLabelWrap: { flexDirection: "row-reverse", alignItems: "center", gap: 8 },
  rowText: { fontSize: 14, color: BRAND_TEXT, textAlign: "right" },
  rowTextActive: { fontWeight: "700", color: BRAND_PRIMARY },
});
