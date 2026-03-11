import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";

export const QuickAddCard = ({ onAdd }: { onAdd: (name: string, qty?: number) => void }) => {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("");

  const handleAdd = () => {
    if (!name.trim()) return;
    onAdd(name, qty ? parseInt(qty) : undefined);
    setName("");
    setQty("");
  };

  return (
    <View style={styles.card}>
      <Text style={styles.title}>הוספה לרשימה</Text>
      <View style={styles.row}>
        <View style={{ width: 70 }}>
          <Text style={styles.label}>כמות</Text>
          <TextInput value={qty} onChangeText={setQty} keyboardType="numeric" style={styles.input} textAlign="right" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.label}>שם מוצר</Text>
          <TextInput value={name} onChangeText={setName} placeholder="מה חסר?" style={styles.input} textAlign="right" />
        </View>
      </View>
      <View style={{ marginTop: 12 }}>
        <PrimaryButton title="הוסף" onPress={handleAdd} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: { backgroundColor: "#FFF", borderRadius: 20, padding: 15, marginBottom: 15, borderWidth: 1, borderColor: "#E5E7EB" },
  title: { fontSize: 16, fontWeight: "800", textAlign: "right", marginBottom: 10 },
  row: { flexDirection: "row-reverse", gap: 10 },
  label: { fontSize: 12, color: "#6B7280", textAlign: "right", marginBottom: 4 },
  input: { backgroundColor: "#F9FAFB", borderWidth: 1, borderColor: "#E5E7EB", borderRadius: 12, padding: 10, textAlign: "right" }
});