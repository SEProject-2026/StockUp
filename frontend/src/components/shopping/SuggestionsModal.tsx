import React from "react";
import { Modal, View, Text, TouchableOpacity, ScrollView, Platform, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { styles, BRAND } from "./styles";

type SuggestionItem = {
  id: string;
  name: string;
  reason?: string;
  type?: 'staple' | 'pairing';
};

type Props = {
  open: boolean;
  onClose: () => void;
  suggestions: SuggestionItem[];
  onAdd: (name: string) => void;
  onDismiss: (id: string) => void;
};

export const SuggestionsModal = ({ open, onClose, suggestions, onAdd, onDismiss }: Props) => {
  const sortedSuggestions = [...suggestions].sort((a, b) => {
    if (a.type === 'staple' && b.type !== 'staple') return -1;
    if (a.type !== 'staple' && b.type === 'staple') return 1;
    return 0;
  });

  return (
    <Modal visible={open} transparent animationType="slide">
      <View style={suggestionRowStyles.backdrop}>
        <TouchableOpacity style={{ flex: 1 }} onPress={onClose} />
        <View style={suggestionRowStyles.sheet}>
          <View style={suggestionRowStyles.handle} />
          
          <View style={suggestionRowStyles.header}>
            <Text style={suggestionRowStyles.title}>✨ הצעות מותאמות אישית</Text>
            <TouchableOpacity onPress={onClose}>
              <Ionicons name="close-circle" size={28} color={BRAND.BORDER} />
            </TouchableOpacity>
          </View>

          <ScrollView 
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 40 }}
          >
            {sortedSuggestions.length === 0 ? (
              <View style={{ padding: 40, alignItems: "center" }}>
                <Ionicons name="sparkles-outline" size={48} color={BRAND.BORDER} />
                <Text style={{ marginTop: 16, color: BRAND.MUTED, textAlign: "center", fontSize: 16 }}>
                  אין המלצות חדשות כרגע.
                </Text>
              </View>
            ) : (
              sortedSuggestions.map((s) => {
                const isStaple = s.type === 'staple';
                return (
                  <View 
                    key={s.id} 
                    style={[
                      suggestionRowStyles.row,
                      isStaple ? suggestionRowStyles.stapleRow : suggestionRowStyles.pairingRow
                    ]}
                  >
                    <TouchableOpacity 
                      style={[
                        suggestionRowStyles.addButton,
                        { backgroundColor: isStaple ? "#6366F1" : BRAND.SUCCESS }
                      ]}
                      onPress={() => onAdd(s.name)}
                    >
                      <Ionicons name="add" size={20} color="#fff" />
                    </TouchableOpacity>

                    <View style={suggestionRowStyles.content}>
                      <View style={{ flexDirection: 'row-reverse', alignItems: 'center' }}>
                        <Ionicons 
                          name={isStaple ? "star" : "link"} 
                          size={12} 
                          color={isStaple ? "#4F46E5" : "#10B981"} 
                          style={{ marginLeft: 4 }}
                        />
                        <Text style={suggestionRowStyles.name}>{s.name}</Text>
                      </View>
                      {!!s.reason && (
                        <Text style={suggestionRowStyles.reason}>{s.reason}</Text>
                      )}
                    </View>

                    <TouchableOpacity 
                      style={suggestionRowStyles.dismissButton}
                      onPress={() => onDismiss(s.id)}
                    >
                      <Ionicons name="trash-outline" size={18} color={BRAND.MUTED} />
                    </TouchableOpacity>
                  </View>
                );
              })
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const suggestionRowStyles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#fff",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: "85%",
    paddingHorizontal: 20,
    paddingTop: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 20,
  },
  handle: {
    width: 40,
    height: 5,
    backgroundColor: "#E5E7EB",
    borderRadius: 3,
    alignSelf: "center",
    marginBottom: 20,
  },
  header: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: "900",
    color: BRAND.TEXT,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 18,
    marginBottom: 10,
    borderWidth: 1,
  },
  stapleRow: {
    backgroundColor: "#F5F3FF", // Light indigo
    borderColor: "#E0E7FF",
  },
  pairingRow: {
    backgroundColor: "#F0FDF4", // Light green
    borderColor: "#DCFCE7",
  },
  name: {
    fontSize: 16,
    fontWeight: "800",
    color: BRAND.TEXT,
    textAlign: "right",
  },
  reason: {
    fontSize: 12,
    color: BRAND.MUTED,
    textAlign: "right",
    marginTop: 2,
  },
  content: {
    flex: 1,
    marginRight: 12,
  },
  addButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 4,
  },
  dismissButton: {
    padding: 8,
  }
});