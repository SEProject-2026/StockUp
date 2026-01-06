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
  onSave: (rowId: string, values: { name: string; quantity: number; expiresAt?: string }) => Promise<void> | void;
};

function pickString(...vals: any[]) {
  for (const v of vals) {
    if (typeof v === "string" && v.trim().length) return v;
  }
  return "";
}

export function EditItemModal({ visible, item, onClose, onSave }: Props) {
  const rowId = useMemo(() => {
    const v =
      item?.id ??
      item?.rowId ??
      item?.key ??
      item?.itemId ??
      item?.productItemId ??
      item?.product_item_id ??
      "";
    return String(v ?? "");
  }, [item]);

  const initialName = useMemo(
    () =>
      pickString(
        item?.nickname,
        item?.name,
        item?.displayName,
        item?.display_name,
        item?.original_name,
        item?.originalName
      ),
    [item]
  );

  const initialQty = useMemo(() => {
    const v = item?.quantity;
    return typeof v === "number" && v > 0 ? String(v) : "1";
  }, [item]);

  const initialExp = useMemo(() => {
    const v = item?.expirationDate ?? item?.expiration_date ?? item?.expiresAt ?? "";
    return typeof v === "string" ? v : "";
  }, [item]);

  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [exp, setExp] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!visible) return;
    setName(initialName);
    setQty(initialQty);
    setExp(initialExp);
    setSaving(false);
  }, [visible, initialName, initialQty, initialExp]);

  if (!visible) return null;

  const qtyNum = Number(qty);
  const canSave = rowId.length > 0 && Number.isFinite(qtyNum) && qtyNum > 0 && !saving;

  return (
    <Modal transparent visible={visible} animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.kav}>
          <View style={styles.card}>
            <View style={styles.header}>
              <Text style={styles.title}>עדכון מוצר</Text>
              <TouchableOpacity onPress={onClose} style={styles.iconBtn} activeOpacity={0.85}>
                <Ionicons name="close" size={18} color="#111827" />
              </TouchableOpacity>
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>שם תצוגה</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder="למשל: חלב טרה"
                placeholderTextColor="#9CA3AF"
                style={styles.input}
                textAlign="right"
              />
            </View>

            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>כמות</Text>
                <TextInput
                  value={qty}
                  onChangeText={setQty}
                  keyboardType={Platform.OS === "ios" ? "number-pad" : "numeric"}
                  placeholder="1"
                  placeholderTextColor="#9CA3AF"
                  style={styles.input}
                  textAlign="right"
                />
              </View>

              <View style={{ width: 10 }} />

              <View style={{ flex: 1 }}>
                <Text style={styles.label}>תוקף (YYYY-MM-DD)</Text>
                <TextInput
                  value={exp}
                  onChangeText={setExp}
                  placeholder="2026-01-05"
                  placeholderTextColor="#9CA3AF"
                  style={styles.input}
                  textAlign="right"
                />
              </View>
            </View>

            <Pressable
              disabled={!canSave}
              style={[styles.saveBtn, !canSave && { opacity: 0.55 }]}
              onPress={async () => {
                try {
                  setSaving(true);
                  const finalName = name.trim().length ? name.trim() : initialName;
                  const finalExp = exp.trim().length ? exp.trim() : undefined;

                  await onSave(rowId, {
                    name: finalName,
                    quantity: qtyNum,
                    expiresAt: finalExp,
                  });
                } finally {
                  setSaving(false);
                }
              }}
            >
              <Text style={styles.saveText}>{saving ? "שומר..." : "שמור"}</Text>
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
    backgroundColor: "rgba(0,0,0,0.35)",
    justifyContent: "center",
    padding: 16,
  },
  kav: { width: "100%", alignItems: "center", justifyContent: "center" },
  card: {
    width: "100%",
    maxWidth: 520,
    borderRadius: 18,
    backgroundColor: "#fff",
    padding: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  header: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  title: { fontSize: 16, fontWeight: "800", color: "#111827", textAlign: "right" },
  iconBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
  },
  field: { marginTop: 10 },
  row: { flexDirection: "row-reverse", marginTop: 10 },
  label: { fontSize: 12, color: "#6B7280", textAlign: "right", marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderColor: "#E5E7EB",
    backgroundColor: "#FAFAFA",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: "#111827",
  },
  saveBtn: {
    marginTop: 12,
    backgroundColor: "#0284C7",
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  saveText: { color: "#fff", fontSize: 14, fontWeight: "800" },
  debugText: { marginTop: 10, fontSize: 11, color: "#6B7280", textAlign: "right" },
});
