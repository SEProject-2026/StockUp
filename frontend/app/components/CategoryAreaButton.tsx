// frontend/app/components/CategoryAreaButton.tsx
import React from "react";
import { Pressable, View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Props = {
  label: "מקרר" | "מקפיא" | "מזווה";
  value: number;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
};

export default function CategoryAreaButton({
  label,
  value,
  icon,
  onPress,
}: Props) {
  const baseColor =
    label === "מקרר"
      ? "#6B8FB3"
      : label === "מקפיא"
      ? "#7BA99C"
      : "#C4956D";

  return (
    <Pressable
      style={[
        styles.container,
        {
          backgroundColor: baseColor + "22",
          borderColor: baseColor,
        },
      ]}
      onPress={onPress}
    >
      <View style={styles.left}>
        <Ionicons name={icon} size={14} color={baseColor} />
        <Text style={[styles.label, { color: baseColor }]}>{label}</Text>
      </View>
      <Text style={[styles.value, { color: baseColor }]}>{value}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    borderRadius: 999,
    borderWidth: 1,
    paddingVertical: 6,
    paddingHorizontal: 10,
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
  },
  left: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 4,
  },
  label: {
    fontSize: 12,
  },
  value: {
    fontSize: 14,
    fontWeight: "600",
  },
});
