import React, { useMemo } from "react";
import { View, Text, StyleSheet, TextInput, Platform, TouchableOpacity, ActivityIndicator } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import type { location } from "./types";
import SuggestionsList from "@/src/components/add-item/SuggestionsList";
import type { CatalogItem } from "@/src/api/catalog";

const BRAND_PRIMARY = "#0284C7";
const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BORDER = "#E5E7EB";

function formatDateLabel(d?: Date) {
  if (!d) return "בחר תאריך";
  return d.toISOString().slice(0, 10);
}

export default function ProductDraftCard(props: {
  editing: boolean;
  barcode: string;
  name: string;
  nickname: string;
  quantity: string;
  location: location;
  expiresAt?: Date;
  locationOptions: Array<{ key: location; label: string; icon: keyof typeof Ionicons.glyphMap }>;

  onChangeBarcode: (v: string) => void;
  onChangeName: (v: string) => void;
  onChangeNickname: (v: string) => void;
  onChangeQuantity: (v: string) => void;

  onPresslocation: () => void;
  onPressScan: () => void;
  onPressDate: () => void;
  onClearDate: () => void;

  onAddToList: () => void;
  onCancelEdit: () => void;
  addDisabled: boolean;

  suggestions: CatalogItem[];
  nameLoading: boolean;

  selectedCatalogItem: CatalogItem | null;
  onClearSelectedCatalogItem: () => void;
  onPickSuggestion: (item: CatalogItem) => void;
}) {
  const meta = useMemo(
    () => props.locationOptions.find((x) => x.key === props.location) ?? props.locationOptions[0],
    [props.location, props.locationOptions]
  );

  const showOriginalUnderNickname = props.nickname.trim().length > 0 && props.selectedCatalogItem?.name;

  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <TouchableOpacity style={styles.chip} activeOpacity={0.85} onPress={props.onPresslocation}>
          <Ionicons name={meta.icon} size={16} color={BRAND_PRIMARY} />
          <Text style={styles.chipText}>{meta.label}</Text>
          <Ionicons name="chevron-down" size={16} color={BRAND_MUTED} />
        </TouchableOpacity>

        <TouchableOpacity style={styles.iconChip} activeOpacity={0.85} onPress={props.onPressScan}>
          <Ionicons name="barcode-outline" size={18} color={BRAND_TEXT} />
          <Text style={styles.iconChipText}>סרוק</Text>
        </TouchableOpacity>
      </View>

      <Field label="שם מוצר (חיפוש)" required>
        <View style={styles.inputRow}>
          <TextInput
            value={props.name}
            onChangeText={props.onChangeName}
            placeholder="התחל להקליד..."
            placeholderTextColor="#9CA3AF"
            style={[styles.input, { flex: 1 }]}
            textAlign="right"
          />

          {props.nameLoading ? (
            <View style={styles.loaderWrap}>
              <ActivityIndicator />
            </View>
          ) : null}
        </View>

        {props.selectedCatalogItem ? (
          <View style={styles.chipRow}>
            <View style={styles.selectedChipBox}>
              <Text style={styles.selectedChipText} numberOfLines={1}>
                {props.selectedCatalogItem.name}
              </Text>
              <TouchableOpacity
                onPress={props.onClearSelectedCatalogItem}
                style={styles.selectedChipX}
                activeOpacity={0.85}
              >
                <Ionicons name="close" size={14} color={BRAND_MUTED} />
              </TouchableOpacity>
            </View>
          </View>
        ) : null}

        {!props.selectedCatalogItem ? (
          <SuggestionsList items={props.suggestions} onPick={props.onPickSuggestion} />
        ) : null}
      </Field>

      <Field label="כינוי במלאי (אופציונלי)">
        <TextInput
          value={props.nickname}
          onChangeText={props.onChangeNickname}
          placeholder="למשל: חלב טרה"
          placeholderTextColor="#9CA3AF"
          style={styles.input}
          textAlign="right"
        />
        {showOriginalUnderNickname ? (
          <Text style={styles.helperText}>יוצג גם השם המקורי מתחת לכינוי במלאי</Text>
        ) : null}
      </Field>

      <View style={styles.row2}>
        <View style={{ flex: 1 }}>
          <Field label="כמות" required>
            <TextInput
              value={props.quantity}
              onChangeText={props.onChangeQuantity}
              placeholderTextColor="#9CA3AF"
              keyboardType={Platform.OS === "ios" ? "number-pad" : "numeric"}
              style={styles.input}
              textAlign="right"
            />
          </Field>
        </View>

        <View style={{ width: 10 }} />

        <View style={{ flex: 1 }}>
          <Field label="תוקף (אופציונלי)">
            <TouchableOpacity activeOpacity={0.85} style={[styles.input, styles.dateInput]} onPress={props.onPressDate}>
              <Text style={[styles.dateText, !props.expiresAt && { color: "#9CA3AF" }]}>
                {formatDateLabel(props.expiresAt)}
              </Text>

              <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                {!!props.expiresAt && (
                  <TouchableOpacity onPress={props.onClearDate} activeOpacity={0.85} style={styles.clearBtn}>
                    <Ionicons name="close" size={14} color={BRAND_MUTED} />
                  </TouchableOpacity>
                )}
                <Ionicons name="calendar-outline" size={18} color={BRAND_MUTED} />
              </View>
            </TouchableOpacity>
          </Field>
        </View>
      </View>

      <Field label="ברקוד (אופציונלי)">
        <TextInput
          value={props.barcode}
          onChangeText={props.onChangeBarcode}
          placeholder="או לסרוק עם הכפתור למעלה"
          placeholderTextColor="#9CA3AF"
          style={styles.input}
          textAlign="right"
        />
      </Field>

      <PrimaryButton
        title={props.editing ? "עדכון פריט ברשימה" : "הוסף לרשימה"}
        onPress={props.onAddToList}
        disabled={props.addDisabled}
        style={[styles.addBtn, props.addDisabled && { opacity: 0.55 }]}
      />

      {props.editing && (
        <TouchableOpacity activeOpacity={0.85} onPress={props.onCancelEdit} style={styles.cancelRow}>
          <Ionicons name="refresh" size={16} color={BRAND_MUTED} />
          <Text style={styles.cancelText}>ביטול עריכה</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <View style={{ gap: 6 }}>
      <Text style={styles.label}>
        {label}
        {required && <Text style={{ color: "#EF4444" }}> *</Text>}
        </Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    borderRadius: 18,
    padding: 12,
    gap: 10,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 999,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#D7EDF9",
  },
  chipText: { fontSize: 12, fontWeight: "800", color: BRAND_TEXT },

  iconChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 999,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  iconChipText: { fontSize: 12, fontWeight: "800", color: BRAND_TEXT },

  label: { fontSize: 12, color: BRAND_MUTED, textAlign: "right", paddingHorizontal: 2 },

  helperText: { fontSize: 12, color: BRAND_MUTED, textAlign: "right", paddingHorizontal: 2, marginTop: 2 },

  input: {
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    backgroundColor: "#FAFAFA",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: BRAND_TEXT,
  },

  inputRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  loaderWrap: { width: 26, alignItems: "center", justifyContent: "center" },

  chipRow: { marginTop: 8, alignItems: "flex-end" },
  selectedChipBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 999,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#D7EDF9",
    maxWidth: "100%",
  },
  selectedChipText: { fontSize: 12, fontWeight: "900", color: BRAND_TEXT, textAlign: "right", maxWidth: 260 },
  selectedChipX: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    alignItems: "center",
    justifyContent: "center",
  },

  row2: { flexDirection: "row", alignItems: "flex-start" },

  dateInput: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8,
  },
  dateText: { fontSize: 14, color: BRAND_TEXT },

  clearBtn: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    alignItems: "center",
    justifyContent: "center",
  },

  addBtn: {
    marginTop: 4,
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },

  cancelRow: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start", paddingHorizontal: 6 },
  cancelText: { fontSize: 12, color: BRAND_MUTED, fontWeight: "700" },
});
