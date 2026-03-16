import React from "react";
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND = {
  TEXT: "#111827",
  MUTED: "#6B7280",
  BORDER: "#E5E7EB",
  PRIMARY: "#0284C7",
  CARD: "#FFFFFF",
};

export const ShoppingListsHeader = ({ newListName, setNewListName, onCreate, creating, listsCount }: any) => (
  <>
    <View style={styles.heroCard}>
      <View style={styles.heroIcon}>
        <Ionicons name="basket-outline" size={22} color={BRAND.PRIMARY} />
      </View>
      <View style={styles.heroTextWrap}>
        <Text style={styles.heroSubtitle}>אפשר ליצור כמה רשימות נפרדות ולנהל כל אחת בנפרד</Text>
      </View>
    </View>

    <View style={styles.createCard}>
      <Text style={styles.createTitle}>יצירת רשימה חדשה</Text>
      {/* ה-inputRow הופך להיות ה"מעטפת" שנראית כמו שדה טקסט */}
      <View style={styles.inputContainer}>
        <TextInput
          value={newListName}
          onChangeText={setNewListName}
          placeholder="שם הרשימה..."
          placeholderTextColor={BRAND.MUTED}
          style={styles.innerInput}
          textAlign="right"
        />
        <TouchableOpacity 
          style={[styles.inlineAddButton, creating && { opacity: 0.7 }]} 
          onPress={onCreate} 
          disabled={creating}
        >
          {creating ? (
            <ActivityIndicator size="small" color={BRAND.PRIMARY} />
          ) : (
            <Ionicons name="add-circle" size={28} color={BRAND.PRIMARY} />
          )}
        </TouchableOpacity>
      </View>
    </View>

    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>הרשימות שלך</Text>
      <Text style={styles.sectionMeta}>{listsCount} רשימות</Text>
    </View>
  </>
);

const styles = StyleSheet.create({
  heroCard: { flexDirection: "row-reverse", alignItems: "center", gap: 12, backgroundColor: "rgba(255,255,255,0.86)", borderRadius: 22, padding: 16, borderWidth: 1, borderColor: "#E6EEF7", marginBottom: 14 },
  heroIcon: { width: 46, height: 46, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: "#F0F9FF" },
  heroTextWrap: { flex: 1 },
  heroTitle: { textAlign: "right", color: BRAND.TEXT, fontWeight: "900", fontSize: 17 },
  heroSubtitle: { marginTop: 4, textAlign: "right", color: BRAND.MUTED, fontWeight: "600", fontSize: 13, lineHeight: 18 },
  createTitle: { textAlign: "right", color: BRAND.TEXT, fontSize: 15, fontWeight: "900", marginBottom: 10 },
  inputRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  input: { flex: 1, height: 46, borderRadius: 14, backgroundColor: "#F9FAFB", borderWidth: 1, borderColor: BRAND.BORDER, paddingHorizontal: 14, color: BRAND.TEXT, fontSize: 14, fontWeight: "700" },
  addButton: { width: 46, height: 46, borderRadius: 14, backgroundColor: BRAND.PRIMARY, alignItems: "center", justifyContent: "center" },
  sectionHeader: { marginBottom: 10, flexDirection: "row-reverse", justifyContent: "space-between", alignItems: "center" },
  sectionTitle: { color: BRAND.TEXT, fontSize: 16, fontWeight: "900" },
  sectionMeta: { color: BRAND.MUTED, fontSize: 13, fontWeight: "700" },
  createCard: { 
    backgroundColor: BRAND.CARD, 
    borderRadius: 20, 
    padding: 16, 
    borderWidth: 1, 
    borderColor: BRAND.BORDER, 
    marginBottom: 16 
  },
  inputContainer: {
    flexDirection: "row-reverse", 
    alignItems: "center",
    backgroundColor: "#F9FAFB",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    height: 52,
    paddingLeft: 8,
  },
  innerInput: {
    flex: 1,
    height: "100%",
    paddingHorizontal: 14,
    color: BRAND.TEXT,
    fontSize: 15,
    fontWeight: "700",
    textAlign: "right",
  },
  inlineAddButton: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
});