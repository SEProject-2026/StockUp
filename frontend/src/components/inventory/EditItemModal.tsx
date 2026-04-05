import React, { useEffect, useMemo, useState } from "react";
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TextInput,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Props = {
  visible: boolean;
  item: any | null;
  onClose: () => void;
  onSave: (values: { 
    nickname: string; 
    quantity: number; 
    expirationDate?: string 
  }) => Promise<void> | void;
};

export function EditItemModal({ visible, item, onClose, onSave }: Props) {
  // השם המקורי שבא מהמערכת - מוצג לקריאה בלבד
  const originalName = useMemo(() => 
    item?.originalName || item?.original_name || "ללא שם מקורי", 
  [item]);

  // הכינוי הנוכחי (במערכת שלך הוא מופיע בשדה name של השורה)
  const initialNickname = useMemo(() => 
    item?.hasNickname ? (item?.name || "") : "", 
  [item]);

  const initialQty = useMemo(() => 
    item?.quantity !== undefined ? String(item.quantity) : "1", 
  [item]);

  const initialExp = useMemo(() => 
    item?.expirationDate || "", 
  [item]);

  const [nickname, setNickname] = useState("");
  const [qty, setQty] = useState("1");
  const [exp, setExp] = useState("");
  const [saving, setSaving] = useState(false);

  // אתחול השדות בכל פעם שהמודל נפתח
  useEffect(() => {
    if (!visible) return;
    setNickname(initialNickname);
    setQty(initialQty);
    setExp(initialExp);
    setSaving(false);
  }, [visible, initialNickname, initialQty, initialExp]);

  if (!visible) return null;

  const qtyNum = Number(qty);
  const canSave = !isNaN(qtyNum) && qtyNum >= 0 && !saving;

  const handleSave = async () => {
    if (!canSave) return;
    try {
      setSaving(true);
      await onSave({
        nickname: nickname.trim(), // יכול להיות ריק
        quantity: qtyNum,
        expirationDate: exp.trim(),
      });
    } catch (error) {
      console.error("Save error:", error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal transparent visible={visible} animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <KeyboardAvoidingView 
          behavior={Platform.OS === "ios" ? "padding" : undefined} 
          style={styles.kav}
        >
          <View style={styles.card}>
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.title}>עריכת מוצר</Text>
              <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                <Ionicons name="close" size={20} color="#111827" />
              </TouchableOpacity>
            </View>

            {/* שדה שם מקורי - לקריאה בלבד */}
            <View style={styles.field}>
              <Text style={styles.label}>שם מקורי</Text>
              <View style={styles.readOnlyContainer}>
                <Ionicons name="lock-closed-outline" size={14} color="#9CA3AF" />
                <Text style={styles.readOnlyText}>{originalName}</Text>
              </View>
            </View>

            {/* שדה כינוי - אופציונלי */}
            <View style={styles.field}>
              <Text style={styles.label}>כינוי אישי (אופציונלי)</Text>
              <TextInput
                value={nickname}
                onChangeText={setNickname}
                placeholder="למשל: חלב לקפה"
                placeholderTextColor="#9CA3AF"
                style={styles.input}
                textAlign="right"
              />
            </View>

            {/* שורת כמות ותוקף */}
            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>כמות</Text>
                <TextInput
                  value={qty}
                  onChangeText={setQty}
                  keyboardType="numeric"
                  style={styles.input}
                  textAlign="right"
                />
              </View>

              <View style={{ width: 12 }} />

              <View style={{ flex: 1.5 }}>
                <Text style={styles.label}>תוקף (YYYY-MM-DD)</Text>
                <TextInput
                  value={exp}
                  onChangeText={setExp}
                  placeholder="2025-12-31"
                  placeholderTextColor="#9CA3AF"
                  style={styles.input}
                  textAlign="right"
                />
              </View>
            </View>

            {/* כפתור שמירה */}
            <Pressable
              disabled={!canSave}
              style={[styles.saveBtn, !canSave && { opacity: 0.6 }]}
              onPress={handleSave}
            >
              <Text style={styles.saveText}>
                {saving ? "שומר שינויים..." : "שמור"}
              </Text>
            </Pressable>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 20,
  },
  kav: {
    width: "100%",
    alignItems: "center",
  },
  card: {
    width: "100%",
    maxWidth: 450,
    backgroundColor: "#FFFFFF",
    borderRadius: 24,
    padding: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  header: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#111827",
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  field: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#4B5563",
    marginBottom: 8,
    textAlign: "right",
  },
  readOnlyContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  readOnlyText: {
    flex: 1,
    fontSize: 15,
    color: "#9CA3AF",
    textAlign: "right",
    marginRight: 8,
  },
  input: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: "#111827",
  },
  row: {
    flexDirection: "row-reverse",
    marginBottom: 24,
  },
  saveBtn: {
    backgroundColor: "#0284C7",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  saveText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
});