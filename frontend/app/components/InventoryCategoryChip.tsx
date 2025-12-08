// app/components/InventoryCategoryChip.tsx
import React from "react";
import { TouchableOpacity, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type InventoryCategoryChipProps = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  styles: any;
};

export function InventoryCategoryChip({
  label,
  icon,
  onPress,
  styles,
}: InventoryCategoryChipProps) {
  return (
    <TouchableOpacity style={styles.inventoryChip} onPress={onPress}>
      <Ionicons name={icon} size={16} color="#2563EB" />
      <Text style={styles.inventoryChipText}>{label}</Text>
    </TouchableOpacity>
  );
}
