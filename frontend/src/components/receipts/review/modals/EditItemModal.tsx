import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, Pressable, Modal, TextInput, Alert, Platform } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import {
  BRAND,
  LOCATION_LABEL,
  LOCATION_ICON,
  PrimaryButtonCompat,
  UnitType,
  formatWeightKg,
  hasWeight as hasWeightFn,
  normalizeUnitType,
} from "../review.shared";
import type { DetectedItem, LocationKey } from "../review.shared";

const SHADOW = Platform.select({
  ios: { shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 10, shadowOffset: { width: 0, height: 6 } },
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
            <Pressable key={opt} onPress={() => props.onChange(opt)} style={[styles.locChip, active && styles.locChipActive]}>
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

  const [unitText, setUnitText] = useState("UNIT");

  const [location, setLocation] = useState<LocationKey>("other");
  const [unitsCount, setUnitsCount] = useState("");

  const hasWeight = !!(item && hasWeightFn(item));

  useEffect(() => {
    if (!item) return;

    setName(item.name ?? "");
    setLocation(item.location ?? "other");

    if (hasWeightFn(item)) {
      const suggestedFromQty =
        Number.isFinite(item.quantity) && item.quantity > 0 ? Math.round(item.quantity) : null;

      setUnitsCount(
        item.units_count && item.units_count > 0
          ? String(item.units_count)
          : suggestedFromQty
          ? String(suggestedFromQty)
          : item.suggested_units && item.suggested_units > 0
          ? String(item.suggested_units)
          : ""
      );

      setQuantity("1");
      setUnitText("KG"); 

    } else {
      setUnitsCount("");
      setQuantity(String(item.quantity ?? 1));
      setUnitText(item.unit ?? "UNIT");
    }
  }, [item]);


  if (!item) return null;

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalOverlay} onPress={onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHeaderRow}>
            <View style={styles.modalTitleWrap}>
              <Text style={styles.modalTitle}>עריכת מוצר</Text>
              <Text style={styles.modalSubtitle}>{hasWeight ? "עדכן שם / יחידות / מיקום" : "עדכן שם / כמות / יחידה / מיקום"}</Text>
            </View>
            <Pressable onPress={onClose} style={styles.modalCloseBtn}>
              <Ionicons name="close" size={18} color={BRAND.TEXT} />
            </Pressable>
          </View>

          <Field label="שם מוצר" value={name} onChangeText={setName} placeholder="למשל: ביצים L" />

          {hasWeight ? (
            <>
              <View style={{ marginTop: 12 }}>
                <Text style={styles.fieldLabel}>משקל שזוהה</Text>
                <View style={styles.readOnlyRow}>
                  <Ionicons name="scale-outline" size={16} color={BRAND.MUTED} />
                  <Text style={styles.readOnlyText}>זוהה {formatWeightKg(item.weight)} ק״ג</Text>
                </View>
              </View>

              <Field
                label="כמה יחידות זה?"
                value={unitsCount}
                onChangeText={setUnitsCount}
                keyboardType={Platform.OS === "ios" ? "number-pad" : "numeric"}
                placeholder={
                  Number.isFinite(item.quantity) && item.quantity > 0
                    ? `הצעה מהסריקה: ${Math.round(item.quantity)}`
                    : item.suggested_units
                    ? `הצעה: ${item.suggested_units}`
                    : "למשל: 6"
                }
              />

            </>
          ) : (
            <>
              <Field
                label="כמות"
                value={quantity}
                onChangeText={setQuantity}
                keyboardType={Platform.OS === "ios" ? "number-pad" : "numeric"}
                placeholder="למשל: 2"
              />

              <Field
                label="יחידה (UNIT / KG)"
                value={unitText}
                onChangeText={setUnitText}
                placeholder="UNIT"
              />
            </>
          )}

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
                const nameOk = name.trim();
                if (!nameOk) {
                  Alert.alert("שגיאה", "ודאי שהשם לא ריק.");
                  return;
                }

                if (hasWeight) {
                  const u = Number(String(unitsCount).replace(",", "."));
                  if (!Number.isFinite(u) || u <= 0) {
                    Alert.alert("שגיאה", "במוצר שקיל חייבים להזין כמה יחידות זה.");
                    return;
                  }

                  onSave({
                    ...item,
                    name: nameOk,
                    location,
                    units_count: Math.round(u),
                    quantity: Math.round(u),     //  final units
                    unit: UnitType.KG,         //  backend expects UNIT/KG
                    // weight stays as is
                  });
                  return;
                }

                const q = Number(String(quantity).replace(",", "."));
                if (!Number.isFinite(q) || q <= 0) {
                  Alert.alert("שגיאה", "ודא שכמות חיובית.");
                  return;
                }

                const normalizedUnit = normalizeUnitType(unitText);

                onSave({
                  ...item,
                  name: nameOk,
                  quantity: Math.round(q),
                  unit: normalizedUnit,
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
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.35)", justifyContent: "center", padding: 16 },
  modalCard: { backgroundColor: BRAND.CARD, borderRadius: 22, padding: 16, borderWidth: 1, borderColor: BRAND.BORDER, ...SHADOW },

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

  readOnlyRow: {
    marginTop: 6,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    backgroundColor: "#F9FAFB",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  readOnlyText: { fontSize: 13, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },

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
