// ItemForm.tsx
import React from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import DateTimePicker from "@react-native-community/datetimepicker";
import { Category } from "@/src/context/inventory-context";

const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_BORDER = "#E5E7EB";

type Props = {
  category: Category;
  onChangeCategory: (c: Category) => void;

  onOpenCategoryPicker: () => void;

  onOpenBarcodeScanner: () => void;

  expiresAt?: Date;
  showDatePicker: boolean;
  onOpenDatePicker: () => void;
  onChangeDate: (event: any, selectedDate?: Date) => void;

  barcode: string;
  name: string;
  quantity: string;
  onChangeBarcode: (v: string) => void;
  onChangeName: (v: string) => void;
  onChangeQuantity: (v: string) => void;
};

function categoryLabel(cat: Category) {
  switch (cat) {
    case "fridge":
      return "מקרר";
    case "freezer":
      return "מקפיא";
    case "pantry":
      return "מזווה";
    case "cleaning supplies":
      return "חומרי ניקוי";
    case "other":
      return "אחר";
    default:
      return "מקרר";
  }
}

function categoryIcon(cat: Category): keyof typeof Ionicons.glyphMap {
  switch (cat) {
    case "fridge":
      return "snow-outline";
    case "freezer":
      return "cube-outline";
    case "pantry":
      return "restaurant-outline";
    case "cleaning supplies":
      return "water-outline";
    case "other":
      return "ellipsis-horizontal-outline";
    default:
      return "pricetag-outline";
  }
}

export default function ItemForm({
  category,
  onOpenCategoryPicker,
  onOpenBarcodeScanner,
  expiresAt,
  showDatePicker,
  onOpenDatePicker,
  onChangeDate,
  barcode,
  name,
  quantity,
  onChangeBarcode,
  onChangeName,
  onChangeQuantity,
}: Props) {
  return (
    <>
      {/* Section: category only */}
      <View style={styles.card}>
        <View style={styles.cardHeaderRow}>
          <View>
            <Text style={styles.cardTitle}>הזנת פריט חדש</Text>
            <Text style={styles.cardSubtitle}>
              בחר קטגוריה והזן פרטי מוצר.
            </Text>
          </View>
          <View style={styles.cardIconCircle}>
            <Ionicons name="create-outline" size={18} color={BRAND_TEXT} />
          </View>
        </View>

        <Text style={styles.fieldLabel}>קטגוריה</Text>
        <TouchableOpacity
          onPress={onOpenCategoryPicker}
          style={styles.selectButton}
          activeOpacity={0.85}
        >
          <View style={styles.selectButtonRight}>
            <Ionicons name={categoryIcon(category)} size={18} color={BRAND_MUTED} />
            <View style={{ flex: 1 }}>
              <Text style={styles.selectButtonHint}>לחצי לבחירת קטגוריה</Text>
              <Text style={styles.selectButtonValue}>{categoryLabel(category)}</Text>
            </View>
          </View>
          <Ionicons name="chevron-down" size={18} color={BRAND_MUTED} />
        </TouchableOpacity>
      </View>

      {/* Section: product details + expiry */}
      <View style={[styles.card, { marginTop: 16 }]}>
        <View style={styles.cardHeaderRow}>
          <Text style={styles.cardTitle}>פרטי המוצר</Text>
          <Ionicons name="cube-outline" size={18} color={BRAND_TEXT} />
        </View>

        <View style={styles.fieldLabelRow}>
          <Text style={styles.fieldLabel}>ברקוד</Text>

          <TouchableOpacity
            onPress={onOpenBarcodeScanner}
            activeOpacity={0.85}
            style={styles.iconButton}
            accessibilityLabel="סריקת ברקוד"
          >
            <Ionicons name="scan-outline" size={20} color={BRAND_MUTED} />
          </TouchableOpacity>
        </View>

        <View style={styles.inputWrap}>
          <Ionicons name="barcode-outline" size={18} color={BRAND_MUTED} />
          <TextInput
            style={styles.input}
            placeholder="סריקת ברקוד או הזנה ידנית"
            placeholderTextColor="#9CA3AF"
            value={barcode}
            onChangeText={onChangeBarcode}
          />
        </View>

        <View style={{ marginTop: 12 }}>
          <Text style={styles.fieldLabel}>שם המוצר</Text>
          <View style={styles.inputWrap}>
            <Ionicons name="pricetag-outline" size={18} color={BRAND_MUTED} />
            <TextInput
              style={styles.input}
              placeholder="לדוגמה: חלב 3%"
              placeholderTextColor="#9CA3AF"
              value={name}
              onChangeText={onChangeName}
            />
          </View>
        </View>

        <View style={{ marginTop: 12 }}>
          <Text style={styles.fieldLabel}>כמות</Text>
          <View style={styles.inputWrap}>
            <Ionicons name="add-circle-outline" size={18} color={BRAND_MUTED} />
            <TextInput
              style={styles.input}
              placeholder="לדוגמה: 2"
              placeholderTextColor="#9CA3AF"
              keyboardType="numeric"
              value={quantity}
              onChangeText={onChangeQuantity}
            />
          </View>
        </View>

        <Text style={[styles.fieldLabel, { marginTop: 16 }]}>תוקף המוצר</Text>

        <TouchableOpacity
          onPress={onOpenDatePicker}
          style={styles.selectButton}
          activeOpacity={0.85}
        >
          <View style={styles.selectButtonRight}>
            <Ionicons name="calendar-outline" size={18} color={BRAND_MUTED} />
            <Text style={styles.selectButtonValue}>
              {expiresAt ? expiresAt.toLocaleDateString("he-IL") : "בחירת תאריך תוקף (לא חובה)"}
            </Text>
          </View>
          <Ionicons name="chevron-down" size={18} color={BRAND_MUTED} />
        </TouchableOpacity>

        {showDatePicker && (
          <View style={styles.datePickerWrapper}>
            <DateTimePicker
              value={expiresAt || new Date()}
              mode="date"
              display={Platform.OS === "android" ? "calendar" : "spinner"}
              onChange={onChangeDate}
              locale="he-IL"
              minimumDate={new Date()}
              themeVariant="light"
            />
          </View>
        )}
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 2,
  },
  cardHeaderRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  cardIconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    textAlign: "right",
    color: BRAND_TEXT,
  },
  cardSubtitle: {
    textAlign: "right",
    color: BRAND_MUTED,
    marginTop: 4,
    fontSize: 12,
  },
  fieldLabelRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    marginBottom: 6,
  },
  fieldLabel: {
    textAlign: "right",
    color: BRAND_TEXT,
    fontSize: 13,
    fontWeight: "600",
  },

  iconButton: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },

  selectButton: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    backgroundColor: "#FFFFFF",
    marginTop: 6,
  },
  selectButtonRight: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
    flex: 1,
  },
  selectButtonHint: {
    fontSize: 11,
    color: BRAND_MUTED,
    textAlign: "right",
  },
  selectButtonValue: {
    fontSize: 14,
    color: BRAND_TEXT,
    textAlign: "right",
    fontWeight: "700",
    flexShrink: 1,
  },

  inputWrap: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  input: {
    flex: 1,
    fontSize: 14,
    textAlign: "right",
    color: BRAND_TEXT,
  },

  datePickerWrapper: {
    marginTop: 10,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#FFFFFF",
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
});
