// src/layout/ScreenHeader.tsx
import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND_TEXT = "#111827";

type Props = {
  title: string;
  onBack?: () => void;
  rightSlot?: React.ReactNode; // למשל אייקון פילטר
};

export default function ScreenHeader({ title, onBack, rightSlot }: Props) {
  return (
    <View style={styles.headerRow}>
      {/* Back button */}
      <TouchableOpacity
        style={styles.headerIconButton}
        onPress={onBack}
      >
        <Ionicons name="chevron-back" size={22} color={BRAND_TEXT} />
      </TouchableOpacity>

      {/* Title */}
      <Text style={styles.title}>{title}</Text>

      {/* Optional right-side content */}
      <View style={styles.rightSlot}>
        {rightSlot ?? <View style={{ width: 32 }} />}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  headerRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 8,
  },
  headerIconButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: BRAND_TEXT,
  },
  rightSlot: {
    width: 32,
    alignItems: "center",
    justifyContent: "center",
  },
});
