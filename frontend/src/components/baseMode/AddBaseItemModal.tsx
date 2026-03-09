import React, { useState } from "react";
import { 
  Modal, 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  Pressable, 
  StyleSheet, 
  Alert, 
  KeyboardAvoidingView, // הוספנו
  Platform,             // הוספנו
  ScrollView            // הוספנו כדי לאפשר גלילה אם הטקסט ארוך
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import { LOCATIONS, locationLabel, locationIcon } from "@/src/hooks/useBaseMode";

const BRAND = { CARD: "#FFFFFF", BORDER: "#E5E7EB", TEXT: "#111827", MUTED: "#6B7280", PRIMARY: "#0284C7" };

export default function AddBaseItemModal(props: { open: boolean; onClose: () => void; onAdd: (item: any) => Promise<void>; }) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [loc, setLoc] = useState<any>("FRIDGE");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    const n = name.trim();
    const q = Number(qty);
    if (!n) return Alert.alert("חסר שם מוצר");
    if (!Number.isFinite(q) || q <= 0) return Alert.alert("כמות לא תקינה");
    try {
      setSubmitting(true);
      await props.onAdd({ name: n, targetQty: q, unit: "יח׳", location: loc });
      setName(""); setQty("1"); setLoc("FRIDGE");
      props.onClose();
    } finally { setSubmitting(false); }
  }

  return (
    <Modal visible={props.open} transparent animationType="slide" onRequestClose={props.onClose}>
      {/* הוספת KeyboardAvoidingView לכל שטח המודאל */}
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"} 
        style={{ flex: 1 }}
      >
        <Pressable style={styles.modalBackdrop} onPress={props.onClose}>
          <Pressable style={styles.modalCard} onPress={(e) => e.stopPropagation()}>
            <View style={styles.modalHandle} />
            
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>הוספת פריט למצב בסיס</Text>
              <TouchableOpacity onPress={props.onClose} style={styles.iconBtn} disabled={submitting}>
                <Ionicons name="close" size={20} color={BRAND.TEXT} />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>הגדירי כמה יחידות באופן אידיאלי צריכות להיות בבית.</Text>
            
            <View style={styles.field}>
              <Text style={styles.label}>שם מוצר</Text>
              <TextInput 
                value={name} 
                onChangeText={setName} 
                placeholder="לדוגמה: קוטג׳" 
                style={styles.input} 
                textAlign="right" 
                editable={!submitting} 
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>כמות רצויה</Text>
              <TextInput 
                value={qty} 
                onChangeText={setQty} 
                keyboardType="numeric" 
                style={styles.input} 
                textAlign="right" 
                editable={!submitting} 
              />
            </View>

            <Text style={styles.label}>מיקום</Text>
            <View style={styles.locationWrap}>
              {LOCATIONS.map((l) => (
                <TouchableOpacity 
                  key={l} 
                  onPress={() => setLoc(l)} 
                  style={[styles.locationOption, loc === l && styles.locationOptionActive]} 
                  disabled={submitting}
                >
                  <Ionicons name={locationIcon(l) as any} size={16} color={loc === l ? BRAND.PRIMARY : BRAND.MUTED} />
                  <Text style={[styles.locationOptionText, loc === l && styles.locationOptionTextActive]}>
                    {locationLabel(l)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <PrimaryButton 
              title={submitting ? "מוסיף..." : "הוסף פריט"} 
              onPress={submit} 
              disabled={submitting} 
            />
          </Pressable>
        </Pressable>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalBackdrop: { 
    flex: 1, 
    backgroundColor: "rgba(17,24,39,0.35)", 
    justifyContent: "flex-end", // גורם למודאל להיצמד לתחתית
    padding: 12 
  },
  modalCard: { 
    backgroundColor: BRAND.CARD, 
    borderRadius: 22, 
    padding: 16, 
    borderWidth: 1, 
    borderColor: BRAND.BORDER,
    paddingBottom: Platform.OS === 'ios' ? 30 : 16 // תוספת פדינג ל-iOS כדי שלא ייצמד לקצה המסך
  },
  modalHandle: { alignSelf: "center", width: 42, height: 5, borderRadius: 999, backgroundColor: "#D1D5DB", marginBottom: 12 },
  modalHeader: { flexDirection: "row-reverse", alignItems: "center", justifyContent: "space-between" },
  modalTitle: { fontSize: 16, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },
  modalSubtitle: { marginTop: 6, marginBottom: 14, color: BRAND.MUTED, fontWeight: "700", fontSize: 12, textAlign: "right", lineHeight: 18 },
  iconBtn: { padding: 6 },
  field: { marginBottom: 12 },
  label: { marginBottom: 6, color: BRAND.MUTED, fontWeight: "800", fontSize: 11.5, textAlign: "right" },
  input: { backgroundColor: "#FAFBFD", borderWidth: 1, borderColor: BRAND.BORDER, borderRadius: 13, paddingHorizontal: 12, paddingVertical: 11, color: BRAND.TEXT, fontWeight: "700", fontSize: 13 },
  locationWrap: { flexDirection: "row-reverse", flexWrap: "wrap", gap: 8, marginBottom: 14 },
  locationOption: { flexDirection: "row-reverse", alignItems: "center", gap: 8, paddingHorizontal: 11, paddingVertical: 9, borderRadius: 999, borderWidth: 1, borderColor: BRAND.BORDER, backgroundColor: "#fff" },
  locationOptionActive: { backgroundColor: "#F4FBFF", borderColor: "rgba(2,132,199,0.35)" },
  locationOptionText: { color: BRAND.MUTED, fontWeight: "800", fontSize: 12 },
  locationOptionTextActive: { color: BRAND.TEXT },
});