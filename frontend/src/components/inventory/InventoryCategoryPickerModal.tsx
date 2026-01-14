// src/features/inventory/components/InventoryCategoryPickerModal.tsx
import React from "react";
import { View, Text, StyleSheet, Modal, Pressable, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { CategoryKey } from "@/src/components/inventory/inventory.utils";
import { CATEGORIES, COLORS } from "./filters.constants";

export default function InventoryCategoryPickerModal(props: {
  open: boolean;
  selectedTab: CategoryKey;
  onClose: () => void;
  onPick: (c: CategoryKey) => void;
}) {
  return (
    <Modal visible={props.open} animationType="fade" transparent onRequestClose={props.onClose}>
      <Pressable style={styles.backdrop} onPress={props.onClose} />

      <View style={styles.sheet}>
        <View style={styles.sheetHeader}>
          <Text style={styles.sheetTitle}>בחירת קטגוריה</Text>
          <TouchableOpacity onPress={props.onClose} activeOpacity={0.8}>
            <Ionicons name="close" size={20} color={COLORS.BRAND_MUTED} />
          </TouchableOpacity>
        </View>

        {CATEGORIES.map((c) => {
          const active = c.key === props.selectedTab;

          return (
            <TouchableOpacity
              key={c.key}
              style={[styles.sheetRow, active && styles.sheetRowActive]}
              onPress={() => props.onPick(c.key)}
              activeOpacity={0.85}
            >
              <View style={styles.sheetRowRight}>
                <View style={styles.sheetRowLabelWrap}>
                  <Text style={[styles.sheetRowText, active && styles.sheetRowTextActive]}>{c.label}</Text>
                  {active && <Ionicons name="checkmark" size={18} color={COLORS.ACCENT} />}
                </View>

                <Ionicons name={c.icon} size={18} color={active ? COLORS.ACCENT : COLORS.BRAND_MUTED} />
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
    borderColor: COLORS.BORDER,
  },

  sheetHeader: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: 8,
  },
  sheetTitle: { fontSize: 14, fontWeight: "700", color: COLORS.BRAND_TEXT, textAlign: "right" },

  sheetRow: { paddingVertical: 12, paddingHorizontal: 10, borderRadius: 12 },
  sheetRowActive: { backgroundColor: COLORS.BRAND_BLUE_SOFT },

  sheetRowRight: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  sheetRowLabelWrap: { flexDirection: "row-reverse", alignItems: "center", gap: 8 },

  sheetRowText: { fontSize: 14, color: COLORS.BRAND_TEXT, textAlign: "right" },
  sheetRowTextActive: { fontWeight: "700", color: COLORS.ACCENT },
});
