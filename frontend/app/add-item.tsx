// frontend/app/add-item.tsx
import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons, MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useInventory, Category } from "./inventory-store";
import DateTimePicker from "@react-native-community/datetimepicker";

export default function AddItemScreen() {
  const { addItem } = useInventory();

  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [category, setCategory] = useState<Category>("fridge");
  const [expiresAt, setExpiresAt] = useState<Date | undefined>(undefined);
  const [showDatePicker, setShowDatePicker] = useState(false);

  const onChangeDate = (event: any, selectedDate?: Date) => {
    // ב-Android: נסגור רק כשהמשתמש לוחץ "OK"
    if (Platform.OS === "android") {
      if (event.type === "set" && selectedDate) {
        setExpiresAt(selectedDate);
      }
      setShowDatePicker(false);
    } else {
      // ב-iOS: מעדכנים תאריך בלי לסגור
      if (selectedDate) {
        setExpiresAt(selectedDate);
      }
    }
  };

  const onAdd = () => {
    if (!name.trim()) {
      Alert.alert("שגיאה", "חייב להיות שם מוצר");
      return;
    }
    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר חיובי");
      return;
    }

    const formattedExpires = expiresAt
      ? expiresAt.toISOString().slice(0, 10)
      : undefined;

    addItem({
      name: name.trim(),
      category,
      quantity: qty,
      expiresAt: formattedExpires,
    });

    router.back();
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 80 : 0}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={() => router.back()}>
            <Ionicons name="chevron-back" size={24} color="#4A3F35" />
          </TouchableOpacity>
          <Text style={styles.title}>הוספת מוצר</Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          {/* כרטיס בחירת אזור ותוקף */}
          <View style={styles.card}>
            <View style={styles.cardHeaderRow}>
              <Text style={styles.cardTitle}>הזנת פריט חדש</Text>
              <Ionicons name="create-outline" size={20} color="#7C6A5A" />
            </View>

            <Text style={styles.cardSubtitle}>בחרי היכן המוצר נמצא</Text>

            <View style={styles.areaRow}>
              <AreaTag
                label="מקרר"
                color="#5B8DEF"
                active={category === "fridge"}
                onPress={() => setCategory("fridge")}
              />
              <AreaTag
                label="מקפיא"
                color="#4EC5C1"
                active={category === "freezer"}
                onPress={() => setCategory("freezer")}
              />
              <AreaTag
                label="מזווה"
                color="#F4A340"
                active={category === "pantry"}
                onPress={() => setCategory("pantry")}
              />
            </View>

            {/* בחירת תאריך תוקף */}
            <Text style={[styles.fieldLabel, { marginTop: 16 }]}>
              תוקף המוצר
            </Text>
            <View style={styles.dateRow}>
              <MaterialIcons name="event" size={20} color="#7C6A5A" />
              <TouchableOpacity
                onPress={() => setShowDatePicker(true)}
                style={styles.dateButton}
              >
                <Text style={styles.dateButtonText}>
                  {expiresAt
                    ? expiresAt.toLocaleDateString("he-IL")
                    : "בחרי תאריך תוקף (לא חובה)"}
                </Text>
              </TouchableOpacity>
            </View>

            {showDatePicker && (
              <View
                style={{
                  backgroundColor: Platform.OS === "ios" ? "#f8f8f6ff" : "transparent",
                  paddingVertical: 8,
                  borderRadius: 12,
                  marginTop: 8,
                }}
              >
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

          {/* פרטי המוצר */}
          <View style={[styles.card, { marginTop: 16 }]}>
            <Text style={styles.cardTitle}>פרטי המוצר</Text>

            <View style={styles.fieldLabelRow}>
              <Text style={styles.fieldLabel}>ברקוד</Text>
              <Ionicons name="barcode-outline" size={18} color="#7C6A5A" />
            </View>
            <TextInput
              style={styles.input}
              placeholder="סריקה או הקלדת ברקוד"
              placeholderTextColor="#A1A1AA"
              value={barcode}
              onChangeText={setBarcode}
            />

            <Text style={styles.fieldLabel}>שם המוצר</Text>
            <TextInput
              style={styles.input}
              placeholder="שם המוצר"
              placeholderTextColor="#A1A1AA"
              value={name}
              onChangeText={setName}
            />

            <Text style={styles.fieldLabel}>כמות</Text>
            <TextInput
              style={styles.input}
              placeholder="כמות"
              placeholderTextColor="#A1A1AA"
              keyboardType="numeric"
              value={quantity}
              onChangeText={setQuantity}
            />
          </View>
        </ScrollView>

        {/* כפתור שמירה */}
        <TouchableOpacity style={styles.addButton} onPress={onAdd}>
          <Ionicons name="checkmark" size={18} color="#FEFCE8" />
          <Text style={styles.addButtonText}>שמירה למלאי</Text>
        </TouchableOpacity>
      </SafeAreaView>
    </KeyboardAvoidingView>
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
        {
          borderColor: color,
          backgroundColor: active ? color : "#FFFFFF",
        },
      ]}
    >
      <Text
        style={[
          styles.areaTagText,
          { color: active ? "#FEFCE8" : "#4A3F35" },
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F7F3ED", // כמו מסך הבית
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
    justifyContent: "space-between",
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#4A3F35",
  },
  container: {
    padding: 16,
    paddingBottom: 90,
    gap: 12,
  },
  card: {
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    padding: 16,
    borderWidth: 1,
    borderColor: "#E0D6C8",
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
  cardTitle: {
    fontSize: 17,
    fontWeight: "600",
    textAlign: "right",
    color: "#4A3F35",
  },
  cardSubtitle: {
    textAlign: "right",
    color: "#7C6A5A",
    marginBottom: 10,
    fontSize: 13,
  },
  areaRow: {
    flexDirection: "row-reverse",
    gap: 8,
    marginBottom: 4,
  },
  areaTag: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
  },
  areaTagText: {
    fontSize: 13,
    fontWeight: "500",
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
    backgroundColor: "#FFF7ED",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E0D6C8",
  },
  dateButtonText: {
    color: "#4A3F35",
    fontSize: 14,
    textAlign: "right",
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
    color: "#4A3F35",
    fontSize: 14,
    fontWeight: "500",
  },
  input: {
    borderRadius: 12,
    backgroundColor: "#FDFDFB",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: "#E4E4E7",
    fontSize: 14,
    textAlign: "right",
  },
  addButton: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 16,
    backgroundColor: "#2563EB",
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: 8,
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowOffset: { width: 0, height: 6 },
    shadowRadius: 12,
    elevation: 4,
  },
  addButtonText: {
    color: "#FEFCE8",
    fontSize: 15,
    fontWeight: "600",
  },
});
