// frontend/app/components/ItemForm.tsx
import React from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from "react-native";
import { Ionicons, MaterialIcons } from "@expo/vector-icons";
import DateTimePicker from "@react-native-community/datetimepicker";
import { Category } from "../../inventory/inventory-store";

const BRAND_PRIMARY = "#0284C7";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_BORDER = "#E5E7EB";

type Props = {
  category: Category;
  onChangeCategory: (c: Category) => void;

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

export default function ItemForm({
  category,
  onChangeCategory,
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
      {/* כרטיס בחירת אזור ותוקף */}
      <View style={styles.card}>
        <View style={styles.cardHeaderRow}>
          <View>
            <Text style={styles.cardTitle}>הזנת פריט חדש</Text>
            <Text style={styles.cardSubtitle}>
              בחרי איפה המוצר נמצא והזיני תוקף.
            </Text>
          </View>
          <View style={styles.cardIconCircle}>
            <Ionicons name="create-outline" size={18} color={BRAND_TEXT} />
          </View>
        </View>

        <Text style={styles.fieldLabel}>אזור בבית</Text>

        <View style={styles.areaRow}>
          <AreaTag
            label="מקרר"
            color="#0284C7"
            active={category === "fridge"}
            onPress={() => onChangeCategory("fridge")}
          />
          <AreaTag
            label="מקפיא"
            color="#6366F1"
            active={category === "freezer"}
            onPress={() => onChangeCategory("freezer")}
          />
          <AreaTag
            label="מזווה"
            color="#F97316"
            active={category === "pantry"}
            onPress={() => onChangeCategory("pantry")}
          />
        </View>

        {/* בחירת תאריך תוקף */}
        <Text style={[styles.fieldLabel, { marginTop: 16 }]}>
          תוקף המוצר
        </Text>
        <View style={styles.dateRow}>
          <MaterialIcons name="event" size={20} color={BRAND_MUTED} />
          <TouchableOpacity onPress={onOpenDatePicker} style={styles.dateButton}>
            <Text style={styles.dateButtonText}>
              {expiresAt
                ? expiresAt.toLocaleDateString("he-IL")
                : "בחרי תאריך תוקף (לא חובה)"}
            </Text>
          </TouchableOpacity>
        </View>

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

      {/* כרטיס פרטי המוצר */}
      <View style={[styles.card, { marginTop: 16 }]}>
        <View style={styles.cardHeaderRow}>
          <Text style={styles.cardTitle}>פרטי המוצר</Text>
          <Ionicons name="cube-outline" size={18} color={BRAND_TEXT} />
        </View>

        <View style={styles.fieldLabelRow}>
          <Text style={styles.fieldLabel}>ברקוד</Text>
          <Ionicons name="barcode-outline" size={18} color={BRAND_MUTED} />
        </View>
        <TextInput
          style={styles.input}
          placeholder="סריקת ברקוד או הזנה ידנית"
          placeholderTextColor="#9CA3AF"
          value={barcode}
          onChangeText={onChangeBarcode}
        />

        <Text style={styles.fieldLabel}>שם המוצר</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={onChangeName}
        />

        <Text style={styles.fieldLabel}>כמות</Text>
        <TextInput
          style={styles.input}
          keyboardType="numeric"
          value={quantity}
          onChangeText={onChangeQuantity}
        />
      </View>
    </>
  );
}

function AreaTag({
  label,
  color,
  active,
  onPress,
}: {
  label: string;
  color: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.areaTag,
        active
          ? { backgroundColor: color, borderColor: color }
          : { backgroundColor: BRAND_BLUE_SOFT, borderColor: BRAND_BORDER },
      ]}
    >
      <Text
        style={[
          styles.areaTagText,
          { color: active ? "#FFFFFF" : BRAND_TEXT },
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
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
    fontWeight: "600",
    textAlign: "right",
    color: BRAND_TEXT,
  },
  cardSubtitle: {
    textAlign: "right",
    color: BRAND_MUTED,
    marginTop: 4,
    fontSize: 12,
  },
  areaRow: {
    flexDirection: "row-reverse",
    gap: 8,
    marginTop: 8,
  },
  areaTag: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  areaTagText: {
    fontSize: 13,
    fontWeight: "500",
  },
  fieldLabelRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
  },
  fieldLabel: {
    textAlign: "right",
    marginTop: 12,
    marginBottom: 4,
    color: BRAND_TEXT,
    fontSize: 13,
    fontWeight: "500",
  },
  input: {
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    fontSize: 14,
    textAlign: "right",
    color: BRAND_TEXT,
  },
  dateRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    marginTop: 6,
  },
  dateButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  dateButtonText: {
    color: BRAND_TEXT,
    fontSize: 14,
    textAlign: "right",
  },
  datePickerWrapper: {
    marginTop: 8,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#FFFFFF",
    paddingVertical: 8,
  },
});
