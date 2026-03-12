import React, { useState } from "react";
import { Modal, View, Text, TextInput, TouchableOpacity, Pressable, KeyboardAvoidingView, Platform, Alert, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LOCATIONS, locationLabel, locationIcon } from "@/src/hooks/useBaseMode";

const BRAND = { PRIMARY: "#0284C7", TEXT: "#111827", MUTED: "#6B7280", BORDER: "#E5E7EB", CARD: "#FFFFFF" };

export default function AddShoppingItemModal({ open, onClose, onAdd }: any) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [loc, setLoc] = useState<any>("FRIDGE");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!name.trim()) return Alert.alert("חסר שם מוצר");
    setSubmitting(true);
    await onAdd({ name: name.trim(), qty: Number(qty), location: loc });
    setSubmitting(false);
    setName(""); setQty("1"); onClose();
  };

  return (
    <Modal visible={open} transparent animationType="slide">
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <Pressable style={styles.backdrop} onPress={onClose}>
          <Pressable style={styles.card} onPress={e => e.stopPropagation()}>
            <Text style={styles.title}>הוספת פריט</Text>
            <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="שם מוצר" textAlign="right" />
            <TextInput style={styles.input} value={qty} onChangeText={setQty} keyboardType="numeric" textAlign="right" />
            <View style={styles.locGrid}>
              {LOCATIONS.map((l: any) => (
                <TouchableOpacity key={l} onPress={() => setLoc(l)} style={[styles.locBtn, loc === l && styles.locBtnActive]}>
                  <Text style={{ color: loc === l ? BRAND.PRIMARY : BRAND.MUTED }}>{locationLabel(l)}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity style={styles.submitBtn} onPress={submit} disabled={submitting}>
              <Text style={styles.submitText}>{submitting ? "מוסיף..." : "הוסף פריט"}</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end", padding: 10 },
  card: { backgroundColor: BRAND.CARD, borderRadius: 20, padding: 20 },
  title: { fontSize: 18, fontWeight: "900", textAlign: "right", marginBottom: 15 },
  input: { backgroundColor: "#F9FAFB", borderWidth: 1, borderColor: BRAND.BORDER, borderRadius: 12, padding: 12, marginBottom: 10 },
  locGrid: { flexDirection: "row-reverse", flexWrap: "wrap", gap: 8, marginBottom: 20 },
  locBtn: { padding: 8, borderRadius: 20, borderWidth: 1, borderColor: BRAND.BORDER },
  locBtnActive: { borderColor: BRAND.PRIMARY, backgroundColor: "#F0F9FF" },
  submitBtn: { backgroundColor: BRAND.PRIMARY, padding: 15, borderRadius: 12, alignItems: "center" },
  submitText: { color: "#fff", fontWeight: "900" }
});