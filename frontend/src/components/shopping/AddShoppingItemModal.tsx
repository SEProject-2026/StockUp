import React, { useState } from "react";
import { Modal, View, Text, TextInput, TouchableOpacity, Pressable, KeyboardAvoidingView, Platform, Alert, ScrollView } from "react-native";
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
  const [loc, setLoc] = useState<LocationKey | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!name.trim()) return Alert.alert("שגיאה", "נא להזין שם מוצר");
    if (!loc) return Alert.alert("שגיאה", "נא לבחור מיקום למוצר");
    
    try {
      setSubmitting(true);
      await onAdd({ name: name.trim(), qty: Number(qty) || 1, location: loc });
      setName(""); 
      setQty("1"); 
      setLoc(null); 
      onClose();
    } finally { 
      setSubmitting(false); 
    }
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
              <TextInput value={name} onChangeText={setName} style={styles.input} textAlign="right" placeholder="מה קונים?" />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>כמות</Text>
              <TextInput value={qty} onChangeText={setQty} keyboardType="numeric" style={styles.input} textAlign="right" />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>מיקום</Text>
              
              {/* כפתור ה-Dropdown */}
              <TouchableOpacity 
                style={[styles.input, { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center' }]} 
                onPress={() => setIsDropdownOpen(!isDropdownOpen)}
              >
                <View style={{ flexDirection: 'row-reverse', alignItems: 'center' }}>
                  {loc ? (
                    <>
                      <Ionicons name={locationIcon(loc as any) as any} size={18} color={BRAND.PRIMARY} style={{ marginLeft: 8 }} />
                      <Text style={{ fontSize: 16 }}>{locationLabel(loc as any)}</Text>
                    </>
                  ) : (
                    <Text style={{ fontSize: 16, color: BRAND.MUTED }}>בחר מיקום...</Text>
                  )}
                </View>
                <Ionicons name={isDropdownOpen ? "chevron-up" : "chevron-down"} size={20} color={BRAND.MUTED} />
              </TouchableOpacity>

              {/* רשימת האפשרויות שנפתחת */}
              {isDropdownOpen && (
                <View style={{ 
                  backgroundColor: '#f9f9f9', 
                  borderRadius: 8, 
                  marginTop: 4, 
                  borderWidth: 1, 
                  borderColor: '#eee',
                  maxHeight: 200,
                  overflow: 'hidden'
                }}>
                  <ScrollView nestedScrollEnabled>
                    {LOCATIONS.map((l) => (
                      <TouchableOpacity 
                        key={l} 
                        style={{ 
                          padding: 12, 
                          flexDirection: 'row-reverse', 
                          alignItems: 'center',
                          borderBottomWidth: 1,
                          borderBottomColor: '#eee'
                        }}
                        onPress={() => {
                          setLoc(l as LocationKey);
                          setIsDropdownOpen(false);
                        }}
                      >
                        <Ionicons name={locationIcon(l as any) as any} size={16} color={BRAND.PRIMARY} style={{ marginLeft: 10 }} />
                        <Text style={{ fontSize: 16, color: loc === l ? BRAND.PRIMARY : '#333' }}>
                          {locationLabel(l as any)}
                        </Text>
                        {loc === l && <Ionicons name="checkmark" size={18} color={BRAND.PRIMARY} style={{ marginRight: 'auto' }} />}
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
              )}
            </View>

            <TouchableOpacity 
              style={[styles.primaryBtn, { marginTop: 20 }, (!name || !loc) && { opacity: 0.6 }]} 
              onPress={submit} 
              disabled={submitting}
            >
              <Text style={styles.primaryBtnText}>{submitting ? "שומר..." : "הוסף לרשימה"}</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </KeyboardAvoidingView>
    </Modal>
  );
}