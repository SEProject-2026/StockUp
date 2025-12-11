// components/inventory/EditItemModal.tsx
import React, { useEffect, useState } from "react";
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Platform,
  Alert,
} from "react-native";
import DateTimePicker from "@react-native-community/datetimepicker";
import { Ionicons } from "@expo/vector-icons";
import { InventoryItem } from "../../inventory/inventory-store";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";

type Props = {
  visible: boolean;
  item: InventoryItem | null;
  onClose: () => void;
  onSave: (
    id: string,
    values: { name: string; quantity: number; expiresAt?: string }
  ) => void;
};

export const EditItemModal: React.FC<Props> = ({
  visible,
  item,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("");
  const [expiresAt, setExpiresAt] = useState<Date | undefined>();
  const [showDatePicker, setShowDatePicker] = useState(false);

  useEffect(() => {
    if (item) {
      setName(item.name);
      setQty(String(item.quantity));
      setExpiresAt(item.expiresAt ? new Date(item.expiresAt) : undefined);
    } else {
      setName("");
      setQty("");
      setExpiresAt(undefined);
      setShowDatePicker(false);
    }
  }, [item, visible]);

  const handleChangeDate = (_: any, selectedDate?: Date) => {
    if (Platform.OS === "android") {
      if (selectedDate) setExpiresAt(selectedDate);
      setShowDatePicker(false);
    } else {
      if (selectedDate) setExpiresAt(selectedDate);
    }
  };

  const handleSave = () => {
    if (!item) return;

    if (!name.trim()) {
      Alert.alert("שגיאה", "חייב להיות שם מוצר");
      return;
    }
    const parsedQty = parseInt(qty, 10);
    if (!Number.isInteger(parsedQty) || parsedQty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר שלם וחיובי");
      return;
    }

    const formattedExpires = expiresAt
      ? expiresAt.toISOString().slice(0, 10)
      : undefined;

    onSave(item.id, {
      name: name.trim(),
      quantity: parsedQty,
      expiresAt: formattedExpires,
    });
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <View style={styles.modalHandle} />
          <Text style={styles.modalTitle}>עריכת מוצר</Text>

          <Text style={styles.modalLabel}>שם המוצר</Text>
          <TextInput
            style={styles.modalInput}
            value={name}
            onChangeText={setName}
            placeholder="שם המוצר"
            placeholderTextColor="#9CA3AF"
            textAlign="right"
          />

          <Text style={styles.modalLabel}>כמות</Text>
          <TextInput
            style={styles.modalInput}
            value={qty}
            onChangeText={setQty}
            keyboardType="numeric"
            placeholder="כמות"
            placeholderTextColor="#9CA3AF"
            textAlign="right"
          />

          <Text style={styles.modalLabel}>תאריך תוקף</Text>
          <TouchableOpacity
            style={styles.modalDateButton}
            onPress={() => setShowDatePicker(true)}
          >
            <Ionicons name="time-outline" size={18} color={BRAND_MUTED} />
            <Text style={styles.modalDateButtonText}>
              {expiresAt
                ? expiresAt.toLocaleDateString("he-IL")
                : "בחר תאריך (לא חובה)"}
            </Text>
          </TouchableOpacity>

          {showDatePicker && (
            <View style={styles.datePickerWrapper}>
              <DateTimePicker
                value={expiresAt || new Date()}
                mode="date"
                display={Platform.OS === "ios" ? "spinner" : "default"}
                onChange={handleChangeDate}
                locale="he-IL"
                minimumDate={new Date()}
                {...(Platform.OS === "ios" ? { themeVariant: "dark" } : {})}
              />
            </View>
          )}

          <View style={styles.modalButtonsRow}>
            <TouchableOpacity style={styles.modalButton} onPress={onClose}>
              <Text style={styles.modalButtonText}>ביטול</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalButton, styles.modalButtonPrimary]}
              onPress={handleSave}
            >
              <Text
                style={[
                  styles.modalButtonText,
                  styles.modalButtonTextPrimary,
                ]}
              >
                שמירה
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.4)",
    alignItems: "center",
    justifyContent: "flex-end",
  },
  modalCard: {
    width: "100%",
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 20,
    paddingBottom: 32,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: -2 },
    shadowRadius: 10,
    elevation: 6,
  },
  modalHandle: {
    alignSelf: "center",
    width: 48,
    height: 4,
    borderRadius: 999,
    backgroundColor: "#E5E7EB",
    marginBottom: 12,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    textAlign: "right",
    marginBottom: 16,
    color: BRAND_TEXT,
  },
  modalLabel: {
    textAlign: "right",
    marginTop: 8,
    marginBottom: 4,
    fontSize: 13,
    color: BRAND_MUTED,
    fontWeight: "500",
  },
  modalInput: {
    borderRadius: 10,
    backgroundColor: BRAND_BLUE_SOFT,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    fontSize: 14,
    color: BRAND_TEXT,
  },
  modalDateButton: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  modalDateButtonText: {
    fontSize: 14,
    color: BRAND_TEXT,
  },
  datePickerWrapper: {
    marginTop: 8,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: BRAND_BLUE_SOFT,
    paddingVertical: 8,
    height: 220,
  },
  modalButtonsRow: {
    flexDirection: "row-reverse",
    gap: 8,
    marginTop: 16,
  },
  modalButton: {
    flex: 1,
    borderRadius: 999,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  modalButtonPrimary: {
    backgroundColor: "#0284C7",
    borderColor: "#0284C7",
  },
  modalButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: BRAND_TEXT,
  },
  modalButtonTextPrimary: {
    color: "#FFFFFF",
  },
});
