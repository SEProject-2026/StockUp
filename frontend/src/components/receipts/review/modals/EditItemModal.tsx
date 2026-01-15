import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, Pressable, Modal, TextInput, Alert, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BRAND, LOCATION_LABEL, LOCATION_ICON, PrimaryButtonCompat } from "../review.shared";
import type { DetectedItem, LocationKey } from "../review.shared";

const SHADOW = Platform.select({
  ios: {
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
  },
  android: { elevation: 2 },
  default: {},
});

function Field(props: {
  label: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  keyboardType?: any;
}) {
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.fieldLabel}>{props.label}</Text>
      <TextInput
        value={props.value}
        onChangeText={props.onChangeText}
        placeholder={props.placeholder}
        keyboardType={props.keyboardType}
        style={styles.input}
        placeholderTextColor="#9CA3AF"
        textAlign="right"
      />
    </View>
  );
}

function LocationSelector(props: { value: LocationKey; onChange: (v: LocationKey) => void }) {
  const options: LocationKey[] = ["fridge", "freezer", "pantry", "cleaning", "other"];
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.fieldLabel}>מיקום בבית</Text>
      <View style={styles.locRow}>
        {options.map((opt) => {
          const active = props.value === opt;
          return (
            <Pressable
              key={opt}
              onPress={() => props.onChange(opt)}
              style={[styles.locChip, active && styles.locChipActive]}
            >
              {LOCATION_ICON[opt]({ size: 16, color: active ? BRAND.BLUE_SOFT : BRAND.TEXT })}
              <Text style={styles.locChipText}>{LOCATION_LABEL[opt]}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export default function EditItemModal(props: {
  item: DetectedItem | null;
  onClose: () => void;
  onSave: (item: DetectedItem) => void;
  onDelete: (id: string) => void;
}) {
  const { item, onClose, onSave, onDelete } = props;

  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unit, setUnit] = useState("");
  const [location, setLocation] = useState<LocationKey>("other");

  useEffect(() => {
    if (!item) return;
    setName(item.name ?? "");
    setQuantity(String(item.quantity ?? 1));
    setUnit(item.unit ?? "");
    setLocation(item.location ?? "other");
  }, [item]);

  if (!item) return null;

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalOverlay} onPress={onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHeaderRow}>
            <View style={styles.modalTitleWrap}>
              <Text style={styles.modalTitle}>עריכת מוצר</Text>
              <Text style={styles.modalSubtitle}>עדכני שם / כמות / יחידה / מיקום</Text>
            </View>
            <Pressable onPress={onClose} style={styles.modalCloseBtn}>
              <Ionicons name="close" size={18} color={BRAND.TEXT} />
            </Pressable>
          </View>

          <Field label="שם מוצר" value={name} onChangeText={setName} placeholder="למשל: ביצים L" />
          <Field
            label="כמות"
            value={quantity}
            onChangeText={setQuantity}
            keyboardType={Platform.OS === "ios" ? "decimal-pad" : "numeric"}
            placeholder="למשל: 2"
          />
          <Field label="יחידה (אופציונלי)" value={unit} onChangeText={setUnit} placeholder="יח׳ / ק״ג / ל׳" />

          <LocationSelector value={location} onChange={setLocation} />

          <View style={styles.modalActionsRow}>
            <Pressable style={styles.dangerBtn} onPress={() => onDelete(item.id)}>
              <Ionicons name="trash-outline" size={18} color={BRAND.TEXT} />
              <Text style={styles.modalBtnText}>מחק</Text>
            </Pressable>

            <View style={{ flex: 1 }} />

            <Pressable style={styles.secondaryBtn} onPress={onClose}>
              <Text style={styles.modalBtnText}>ביטול</Text>
            </Pressable>
          </View>

          <View style={{ marginTop: 12 }}>
            <PrimaryButtonCompat
              title="שמור"
              onPress={() => {
                const q = Number(String(quantity).replace(",", "."));
                if (!name.trim() || !Number.isFinite(q) || q <= 0) {
                  Alert.alert("שגיאה", "ודאי שהשם לא ריק ושכמות חיובית.");
                  return;
                }
                onSave({
                  ...item,
                  name: name.trim(),
                  quantity: q,
                  unit: unit.trim() || undefined,
                  location,
                });
              }}
              leftIcon={<Ionicons name="save-outline" size={18} color={BRAND.TEXT} />}
            />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.35)",
    justifyContent: "center",
    padding: 16,
  },
  modalCard: {
    backgroundColor: BRAND.CARD,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    ...SHADOW,
  },
  modalHeaderRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  modalTitleWrap: { flex: 1 },
  modalTitle: { fontSize: 16, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },
  modalSubtitle: { fontSize: 12, color: BRAND.MUTED, textAlign: "right", marginTop: 2 },
  modalCloseBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: BRAND.BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND.BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },

  fieldLabel: { marginTop: 2, fontSize: 12, color: BRAND.MUTED, textAlign: "right" },
  input: {
    marginTop: 6,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    backgroundColor: "#FAFAFA",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: BRAND.TEXT,
  },

  modalActionsRow: { flexDirection: "row-reverse", alignItems: "center", gap: 8, marginTop: 16 },
  dangerBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: BRAND.BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#0284C7",
  },
  secondaryBtn: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: BRAND.BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND.BLUE_LINE,
  },
  modalBtnText: { fontSize: 13, fontWeight: "900", color: BRAND.TEXT },

  locRow: { flexDirection: "row-reverse", flexWrap: "wrap", gap: 8, marginTop: 10 },
  locChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 11,
    borderRadius: 14,
    backgroundColor: BRAND.CARD,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },
  locChipActive: { backgroundColor: BRAND.BLUE_SOFT, borderColor: "#0284C7" },
  locChipText: { fontSize: 12, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },
});
