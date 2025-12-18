import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND_PRIMARY = "#0284C7";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";

type Props = {
  onPress: () => void;
};

export default function AddHomeCard({ onPress }: Props) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.9} style={[styles.card, styles.addCard]}>
      <View style={styles.addInner}>
        <View style={styles.addIcon}>
          <Ionicons name="add" size={22} color={BRAND_PRIMARY} />
        </View>
        <Text style={styles.addTitle}>הוספת בית</Text>
        <Text style={styles.addSubtitle} numberOfLines={2}>
          צרי בית חדש למלאי משותף
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: 18,
    padding: 14,
    aspectRatio: 1,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
  },

  addCard: {
    borderStyle: "dashed",
    borderWidth: 2,
    borderColor: "rgba(2,132,199,0.35)",
    backgroundColor: "rgba(2,132,199,0.06)",
    alignItems: "center",
    justifyContent: "center",
  },

  addInner: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 8,
  },

  addIcon: {
    width: 56,
    height: 56,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.95)",
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.18)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 10,
  },

  addTitle: {
    fontSize: 15,
    fontWeight: "900",
    color: TEXT,
    textAlign: "center",
  },

  addSubtitle: {
    marginTop: 6,
    fontSize: 12,
    color: MUTED,
    textAlign: "center",
    lineHeight: 16,
  },
});
