import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { DraftItem, location } from "./types";

const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BORDER = "#E5E7EB";
const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_PRIMARY = "#0284C7";
const BRAND_PINK = "#FF4FA3";
const BRAND_PINK_SOFT = "#FFE0EF";

export default function PendingList(props: {
  items: DraftItem[];
  locationOptions: Array<{ key: location; label: string }>;
  onEdit: (item: DraftItem) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <View style={{ gap: 10 }}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>הרשימה להוספה</Text>
        <Text style={styles.subtitle}>{props.items.length} פריטים</Text>
      </View>

      {props.items.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="list-outline" size={18} color={BRAND_MUTED} />
          <Text style={styles.emptyText}>הוסף פריטים לרשימה ואז שמור הכל יחד.</Text>
        </View>
      ) : (
        props.items.map((item) => (
          <View key={item.id} style={styles.row}>
            <TouchableOpacity style={{ flex: 1 }} activeOpacity={0.85} onPress={() => props.onEdit(item)}>
              <Text style={styles.name} numberOfLines={1}>
                {item.name}
              </Text>
              <Text style={styles.meta}>
                כמות: {item.quantity} •{" "}
                {props.locationOptions.find((x) => x.key === item.location)?.label ?? "קטגוריה"}
                {item.barcode ? " • ברקוד" : ""}
                {item.expiresAt ? " • תוקף" : ""}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => props.onEdit(item)} activeOpacity={0.85} style={styles.iconBtn}>
              <Ionicons name="create-outline" size={18} color={BRAND_PRIMARY} />
            </TouchableOpacity>

            <TouchableOpacity onPress={() => props.onRemove(item.id)} activeOpacity={0.85} style={[styles.iconBtn, { backgroundColor: BRAND_PINK_SOFT }]}>
              <Ionicons name="trash-outline" size={18} color={BRAND_PINK} />
            </TouchableOpacity>
          </View>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  headerRow: {
    marginTop: 2,
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
  },
  title: { fontSize: 14, fontWeight: "800", color: BRAND_TEXT },
  subtitle: { fontSize: 12, color: BRAND_MUTED },

  emptyCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  emptyText: { flex: 1, color: BRAND_MUTED, textAlign: "right", fontSize: 12 },

  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  name: { fontSize: 14, fontWeight: "800", color: BRAND_TEXT, textAlign: "right" },
  meta: { marginTop: 3, fontSize: 12, color: BRAND_MUTED, textAlign: "right" },

  iconBtn: {
    width: 38,
    height: 38,
    borderRadius: 999,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },
});
