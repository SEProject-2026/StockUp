import React, { useState } from "react";
import { Modal, View, Text, TextInput, TouchableOpacity, Pressable, KeyboardAvoidingView, Platform, Alert, ScrollView } from "react-native";
import { styles, BRAND } from "./styles";
import { type LocationKey } from "@/src/hooks/shopping/useShoppingList";

type Props = {
  open: boolean;
  onClose: () => void;
  onAdd: (payload: { name: string; qty: number; location: LocationKey }) => Promise<void> | void;
  existingCategories?: string[];
};

export function AddShoppingItemModal({ open, onClose, onAdd, existingCategories = [] }: Props) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [loc, setLoc] = useState<LocationKey>("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) return Alert.alert("שגיאה", "נא להזין שם מוצר");
    try {
      setSubmitting(true);
      await onAdd({ name: name.trim(), qty: Number(qty) || 1, location: loc });
      setName(""); setQty("1"); setLoc(""); onClose();
    } finally { setSubmitting(false); }
  }

  const suggestionList = existingCategories.filter(c => c && c !== "UNSORTED" && c !== "OTHER");

  return (
    <Modal visible={open} transparent animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <Pressable style={styles.modalBackdrop} onPress={onClose}>
          <Pressable style={styles.modalCard} onPress={e => e.stopPropagation()}>
            <View style={styles.modalHandle} />
            <Text style={styles.modalTitle}>הוספת פריט (בחרי קטגוריה)</Text>

            <View style={styles.field}>
              <Text style={styles.label}>שם מוצר</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                style={styles.input}
                textAlign="right"
                placeholder="מה לקנות?"
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>כמות</Text>
              <TextInput
                value={qty}
                onChangeText={setQty}
                keyboardType="numeric"
                style={styles.input}
                textAlign="right"
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>קטגוריה (למשל: ירקות, משקאות...)</Text>
              <TextInput
                value={loc}
                onChangeText={setLoc}
                style={styles.input}
                textAlign="right"
                placeholder="איפה זה נמצא?"
              />

              {suggestionList.length > 0 && (
                <View style={{ marginTop: 8 }}>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingLeft: 4 }}>
                    {suggestionList.map((cat) => (
                      <TouchableOpacity
                        key={cat}
                        style={[
                          styles.chip,
                          loc === cat && { backgroundColor: BRAND.PRIMARY, borderColor: BRAND.PRIMARY }
                        ]}
                        onPress={() => setLoc(cat)}
                      >
                        <Text style={[styles.chipText, loc === cat && { color: "#fff" }]}>{cat}</Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
              )}
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