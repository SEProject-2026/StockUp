import React, { useState } from "react";
import { Modal, View, Text, TextInput, TouchableOpacity, Pressable, KeyboardAvoidingView, Platform, Alert } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LOCATIONS, locationLabel, locationIcon } from "@/src/hooks/useBaseMode";
import { styles, BRAND } from "./styles";
import { type LocationKey } from "@/src/hooks/useShoppingList";

type Props = {
  open: boolean;
  onClose: () => void;
  onAdd: (payload: { name: string; qty: number; location: LocationKey }) => Promise<void> | void;
};

export function AddShoppingItemModal({ open, onClose, onAdd }: Props) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [loc, setLoc] = useState<LocationKey>("FRIDGE");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) return Alert.alert("שגיאה", "נא להזין שם מוצר");
    try {
      setSubmitting(true);
      await onAdd({ name: name.trim(), qty: Number(qty) || 1, location: loc });
      setName(""); setQty("1"); onClose();
    } finally { setSubmitting(false); }
  }

  return (
    <Modal visible={open} transparent animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <Pressable style={styles.modalBackdrop} onPress={onClose}>
          <Pressable style={styles.modalCard} onPress={e => e.stopPropagation()}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>הוספת פריט חדש</Text>
            
            <View style={styles.field}>
              <Text style={styles.label}>שם מוצר</Text>
              <TextInput value={name} onChangeText={setName} style={styles.input} textAlign="right" />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>כמות</Text>
              <TextInput value={qty} onChangeText={setQty} keyboardType="numeric" style={styles.input} textAlign="right" />
            </View>

            <Text style={styles.label}>מיקום</Text>
            <View style={styles.locationWrap}>
              {LOCATIONS.map((l) => (
                <TouchableOpacity 
                  key={l} 
                  onPress={() => setLoc(l as LocationKey)} 
                  style={[styles.locationOption, loc === l && styles.locationOptionActive]}
                >
                  <Ionicons name={locationIcon(l as any) as any} size={14} color={loc === l ? BRAND.PRIMARY : BRAND.MUTED} />
                  <Text style={[styles.locationOptionText, loc === l && styles.locationOptionTextActive]}>{locationLabel(l as any)}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity style={styles.primaryBtn} onPress={submit} disabled={submitting}>
              <Text style={styles.primaryBtnText}>{submitting ? "שומר..." : "הוסף לרשימה"}</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </KeyboardAvoidingView>
    </Modal>
  );
}