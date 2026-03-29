import React from "react";
import { Modal, View, Text, TouchableOpacity, ScrollView, Platform, StyleSheet, KeyboardAvoidingView, TextInput } from "react-native";
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
  onAdd: (name: string, location: string) => void;
  onDismiss: (id: string) => void;
  existingCategories?: string[];
};

export const SuggestionsModal = ({ open, onClose, suggestions, onAdd, onDismiss, existingCategories = [] }: Props) => {
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [customLoc, setCustomLoc] = React.useState("");

  const sortedSuggestions = [...suggestions].sort((a, b) => {
    if (a.type === 'staple' && b.type !== 'staple') return -1;
    if (a.type !== 'staple' && b.type === 'staple') return 1;
    return 0;
  });

  const categoryList = Array.from(new Set([...existingCategories, "אחר"])).filter(c => c && c !== "UNSORTED" && c !== "OTHER");

  function handleAdd(name: string, location: string) {
    const finalLoc = customLoc.trim() || (location === "אחר" ? "OTHER" : location);
    onAdd(name, finalLoc);
    setActiveId(null);
    setCustomLoc("");
  }

  return (
    <Modal visible={open} transparent animationType="slide">
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"} 
        style={{ flex: 1 }}
      >
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
              keyboardShouldPersistTaps="handled"
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
                  const isActive = activeId === s.id;

                  return (
                    <View key={s.id}>
                      <View 
                        style={[
                          suggestionRowStyles.row,
                          isStaple ? suggestionRowStyles.stapleRow : suggestionRowStyles.pairingRow,
                          isActive && { borderBottomLeftRadius: 0, borderBottomRightRadius: 0, marginBottom: 0 }
                        ]}
                      >
                        <TouchableOpacity 
                          style={[
                            suggestionRowStyles.addButton,
                            { backgroundColor: isStaple ? "#6366F1" : BRAND.SUCCESS }
                          ]}
                          onPress={() => {
                             setActiveId(isActive ? null : s.id);
                             setCustomLoc("");
                          }}
                        >
                          <Ionicons name={isActive ? "chevron-up" : "add"} size={20} color="#fff" />
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

                      {isActive && (
                        <View style={[
                          suggestionRowStyles.categorySelector,
                          isStaple ? { backgroundColor: "#EEF2FF" } : { backgroundColor: "#F0FDF4" }
                        ]}>
                          <Text style={suggestionRowStyles.selectorTitle}>בחרי קטגוריה:</Text>
                          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
                            {categoryList.map(cat => (
                              <TouchableOpacity 
                                key={cat} 
                                style={suggestionRowStyles.categoryChip}
                                onPress={() => handleAdd(s.name, cat)}
                              >
                                <Text style={suggestionRowStyles.categoryChipText}>{cat}</Text>
                              </TouchableOpacity>
                            ))}
                          </ScrollView>

                          <View style={suggestionRowStyles.customInputContainer}>
                            <TextInput 
                              style={suggestionRowStyles.customInput}
                              placeholder="או קטגוריה חדשה..."
                              value={customLoc}
                              onChangeText={setCustomLoc}
                              textAlign="right"
                            />
                            {customLoc.trim().length > 0 && (
                              <TouchableOpacity 
                                style={suggestionRowStyles.confirmBtn}
                                onPress={() => handleAdd(s.name, customLoc)}
                              >
                                <Ionicons name="checkmark-circle" size={24} color={BRAND.PRIMARY} />
                              </TouchableOpacity>
                            )}
                          </View>
                        </View>
                      )}
                    </View>
                  );
                })
              )}
            </ScrollView>
          </View>
        </View>
      </KeyboardAvoidingView>
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
    backgroundColor: "#F5F3FF",
    borderColor: "#E0E7FF",
  },
  pairingRow: {
    backgroundColor: "#F0FDF4",
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
  },
  categorySelector: {
    padding: 12,
    paddingTop: 0,
    borderBottomLeftRadius: 18,
    borderBottomRightRadius: 18,
    marginBottom: 10,
    marginTop: -1,
    borderWidth: 1,
    borderTopWidth: 0,
    borderColor: "#E5E7EB",
  },
  selectorTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: BRAND.MUTED,
    marginBottom: 8,
    textAlign: "right",
  },
  categoryChip: {
    backgroundColor: "#fff",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: "600",
    color: BRAND.TEXT,
  },
  customInputContainer: {
    flexDirection: "row-reverse",
    alignItems: "center",
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: "rgba(0,0,0,0.05)",
    paddingTop: 12,
  },
  customInput: {
    flex: 1,
    backgroundColor: "#fff",
    height: 36,
    borderRadius: 10,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    fontSize: 14,
    color: BRAND.TEXT,
  },
  confirmBtn: {
    marginLeft: 8,
  }
});