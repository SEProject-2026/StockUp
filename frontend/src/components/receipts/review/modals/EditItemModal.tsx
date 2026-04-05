import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Modal,
  TextInput,
  Alert,
  Platform,
  Keyboard,
  TouchableWithoutFeedback,
  ScrollView,
} from "react-native";
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
  onBlur?: () => void;
}) {
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.fieldLabel}>{props.label}</Text>
      <TextInput
        value={props.value}
        onChangeText={props.onChangeText}
        placeholder={props.placeholder}
        keyboardType={props.keyboardType}
        onBlur={props.onBlur}
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
              onPress={() => {
                Keyboard.dismiss();
                props.onChange(opt);
              }}
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

  const [originalName, setOriginalName] = useState("");
  const [nickname, setNickname] = useState(""); // שדה הכינוי החדש
  const [quantity, setQuantity] = useState("1");
  const [unitText, setUnitText] = useState("UNIT");
  const [location, setLocation] = useState<LocationKey>("other");
  const [unitsCount, setUnitsCount] = useState("");

  const hasWeight = !!(item && hasWeightFn(item));

  useEffect(() => {
    if (!item) return;

    setOriginalName(item.name ?? "");
    setNickname(item.nickname ?? ""); // טעינת כינוי קיים אם יש
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

  const closeModal = () => {
    Keyboard.dismiss();
    onClose();
  };

  return (
    <Modal visible transparent animationType="fade" onRequestClose={closeModal}>
      <Pressable style={styles.modalOverlay} onPress={closeModal}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
            <ScrollView
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
              contentContainerStyle={{ paddingBottom: 4 }}
            >
              <View style={styles.modalHeaderRow}>
                <View style={styles.modalTitleWrap}>
                  <Text style={styles.modalTitle}>עריכת מוצר</Text>
                  <Text style={styles.modalSubtitle}>עדכן כינוי, כמות ומיקום</Text>
                </View>
                <Pressable onPress={closeModal} style={styles.modalCloseBtn}>
                  <Ionicons name="close" size={18} color={BRAND.TEXT} />
                </Pressable>
              </View>

              {/* שם מוצר מקורי - נעול לעריכה */}
              <View style={{ marginTop: 12 }}>
                <Text style={styles.fieldLabel}>שם מוצר (לא ניתן לשינוי)</Text>
                <View style={styles.readOnlyNameField}>
                   <Text style={styles.readOnlyNameText}>{originalName}</Text>
                </View>
              </View>

              {/* שדה כינוי חדש */}
              <Field 
                label="כינוי למוצר" 
                value={nickname} 
                onChangeText={setNickname} 
              />

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
                    onBlur={() => Keyboard.dismiss()}
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
                    onBlur={() => Keyboard.dismiss()}
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
                <Pressable
                  style={styles.dangerBtn}
                  onPress={() => {
                    Keyboard.dismiss();
                    onDelete(item.id);
                  }}
                >
                  <Ionicons name="trash-outline" size={18} color={BRAND.TEXT} />
                  <Text style={styles.modalBtnText}>מחק</Text>
                </Pressable>

                <View style={{ flex: 1 }} />

                <Pressable style={styles.secondaryBtn} onPress={closeModal}>
                  <Text style={styles.modalBtnText}>ביטול</Text>
                </Pressable>
              </View>

              <View style={{ marginTop: 12 }}>
                <PrimaryButtonCompat
                  title="שמור"
                  onPress={() => {
                    Keyboard.dismiss();

                    // אובייקט בסיס לעדכון
                    const baseUpdate = {
                      ...item,
                      name: originalName, // השם המקורי נשאר כפי שהוא
                      nickname: nickname.trim(), // הכינוי החדש
                      location,
                    };

                    if (hasWeight) {
                      const u = Number(String(unitsCount).replace(",", "."));
                      if (!Number.isFinite(u) || u <= 0) {
                        Alert.alert("שגיאה", "במוצר שקיל חייבים להזין כמה יחידות זה.");
                        return;
                      }

                      onSave({
                        ...baseUpdate,
                        units_count: Math.round(u),
                        quantity: Math.round(u),
                        unit: UnitType.KG,
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
                      ...baseUpdate,
                      quantity: Math.round(q),
                      unit: normalizedUnit,
                    });
                  }}
                  leftIcon={<Ionicons name="save-outline" size={18} color={BRAND.TEXT} />}
                />
              </View>
            </ScrollView>
          </TouchableWithoutFeedback>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.35)", justifyContent: "center", padding: 16 },

  modalCard: {
    backgroundColor: BRAND.CARD,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    ...SHADOW,
    maxHeight: "85%",
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

  // סגנון חדש לשדה השם הנעול
  readOnlyNameField: {
    marginTop: 6,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    backgroundColor: "#F3F4F6", // צבע רקע אפור יותר
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    opacity: 0.8,
  },
  readOnlyNameText: {
    fontSize: 14,
    color: BRAND.MUTED,
    textAlign: "right",
    fontWeight: "600",
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