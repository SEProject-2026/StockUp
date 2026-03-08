import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const BRAND = { PRIMARY: "#0284C7", DANGER: "#DC2626", TEXT: "#111827", MUTED: "#6B7280", NOTE_LINE: "#E8EDF5" };

interface Props {
  item: any;
  mode: "EDIT" | "SHOPPING";
  isPicked: boolean;
  onToggle: () => void;
  onRemove: () => void;
  onUpdateQty: (delta: number) => void;
}

export const ShoppingItemRow = ({ item, mode, isPicked, onToggle, onRemove, onUpdateQty }: Props) => {
  return (
    <View style={[styles.noteRow, isPicked && mode === "SHOPPING" && { opacity: 0.6 }]}>
      <View style={styles.actions}>
        {mode === "SHOPPING" ? (
          <TouchableOpacity onPress={onToggle} style={[styles.checkBtn, isPicked && styles.checkBtnActive]}>
            {isPicked && <Ionicons name="checkmark" size={16} color="#fff" />}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity onPress={onRemove} style={styles.removeBtn}>
            <Ionicons name="trash-outline" size={16} color="#DC2626" />
          </TouchableOpacity>
        )}

        {/* בקר כמות (Stepper) */}
        <View style={styles.stepperContainer}>
          {mode === "EDIT" && (
            <TouchableOpacity onPress={() => onUpdateQty(1)} style={styles.stepBtn}>
              <Ionicons name="add" size={14} color="#0284C7" />
            </TouchableOpacity>
          )}
          
          <View style={styles.qtyPill}>
            <Text style={styles.qtyText}>{item.quantity || 1}</Text>
          </View>

          {mode === "EDIT" && (
            <TouchableOpacity onPress={() => onUpdateQty(-1)} style={styles.stepBtn}>
              <Ionicons name="remove" size={14} color="#0284C7" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      <View style={styles.textWrap}>
        <Text style={[styles.title, isPicked && mode === "SHOPPING" && styles.strike]}>
          {item.name}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  noteRow: { minHeight: 60, borderBottomWidth: 1, borderBottomColor: BRAND.NOTE_LINE, paddingHorizontal: 15, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  actions: { flexDirection: "row", alignItems: "center", gap: 10 },
  checkBtn: { width: 28, height: 28, borderRadius: 8, borderWidth: 1.5, borderColor: BRAND.PRIMARY, alignItems: "center", justifyContent: "center" },
  checkBtnActive: { backgroundColor: BRAND.PRIMARY },
  removeBtn: { width: 32, height: 32, borderRadius: 10, backgroundColor: "#F9FAFB", alignItems: "center", justifyContent: "center" },
  qtyPill: {
    minWidth: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  qtyText: {
    fontSize: 13,
    fontWeight: "900",
    color: "#111827",
  },
  textWrap: { flex: 1, alignItems: "flex-end", marginLeft: 15 },
  title: { fontSize: 15, fontWeight: "700", color: BRAND.TEXT },
  strike: { textDecorationLine: "line-through", color: BRAND.MUTED },
  source: { fontSize: 10, color: BRAND.PRIMARY, marginTop: 2 },
  stepperContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
    padding: 2,
    gap: 4,
  },
  stepBtn: {
    width: 24,
    height: 24,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFF",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
});