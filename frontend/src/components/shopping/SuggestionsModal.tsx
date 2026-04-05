import React, { useState, useMemo } from "react";
import { Modal, View, Text, TouchableOpacity, TextInput, FlatList, Pressable, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND = { BG: "#F4F4F4", CARD: "#FFFFFF", BORDER: "#E5E7EB", TEXT: "#111827", MUTED: "#6B7280", PRIMARY: "#0284C7", PRIMARY_SOFT: "#E5F3FF" };

interface Props {
  open: boolean;
  onClose: () => void;
  suggestions: any[];
  existingNamesSet: Set<string>;
  onAdd: (name: string) => void;
}

export const SuggestionsModal = ({ open, onClose, suggestions, existingNamesSet, onAdd }: Props) => {
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    const base = suggestions.filter(s => !existingNamesSet.has(s.name.trim().toLowerCase()));
    if (!query) return base;
    return base.filter(s => s.name.toLowerCase().includes(query));
  }, [q, suggestions, existingNamesSet]);

  return (
    <Modal visible={open} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalBackdrop} onPress={onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHandle} />
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>המלצות למוצרים</Text>
            <TouchableOpacity onPress={onClose} style={styles.iconBtn}>
              <Ionicons name="close" size={20} color={BRAND.TEXT} />
            </TouchableOpacity>
          </View>

          <View style={styles.searchCard}>
            <Ionicons name="search" size={18} color={BRAND.MUTED} />
            <TextInput value={q} onChangeText={setQ} placeholder="חיפוש בהמלצות..." style={styles.searchInput} textAlign="right" />
          </View>

          <FlatList
            data={filtered}
            keyExtractor={(x) => x.id}
            renderItem={({ item: s }) => (
              <View style={styles.suggestionRow}>
                <TouchableOpacity onPress={() => onAdd(s.name)} style={styles.addMiniBtn}>
                  <Ionicons name="add" size={15} color={BRAND.PRIMARY} />
                  <Text style={styles.addMiniText}>הוסף</Text>
                </TouchableOpacity>
                <View style={styles.suggestionTextWrap}>
                  <Text style={styles.suggestionName}>{s.name}</Text>
                  {!!s.reason && <Text style={styles.suggestionReason}>{s.reason}</Text>}
                </View>
              </View>
            )}
            ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          />
        </Pressable>
      </Pressable>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalBackdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end", padding: 12 },
  modalCard: { backgroundColor: "#FFF", borderRadius: 22, padding: 16, maxHeight: "80%" },
  modalHandle: { alignSelf: "center", width: 40, height: 5, borderRadius: 10, backgroundColor: "#DDD", marginBottom: 15 },
  modalHeader: { flexDirection: "row-reverse", justifyContent: "space-between", alignItems: "center", marginBottom: 15 },
  modalTitle: { fontSize: 18, fontWeight: "900" },
  searchCard: { flexDirection: "row-reverse", alignItems: "center", backgroundColor: "#F3F4F6", borderRadius: 12, paddingHorizontal: 10, marginBottom: 15 },
  searchInput: { flex: 1, paddingVertical: 10, fontSize: 14 },
  suggestionRow: { flexDirection: "row-reverse", alignItems: "center", padding: 12, borderWidth: 1, borderColor: "#EEE", borderRadius: 15 },
  suggestionTextWrap: { flex: 1, alignItems: "flex-end" },
  suggestionName: { fontWeight: "800", color: "#111" },
  suggestionReason: { fontSize: 11, color: "#666" },
  addMiniBtn: { flexDirection: "row-reverse", alignItems: "center", gap: 5, backgroundColor: "#E5F3FF", paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 },
  addMiniText: { color: "#0284C7", fontWeight: "bold", fontSize: 12 },
  iconBtn: { padding: 5 }
});