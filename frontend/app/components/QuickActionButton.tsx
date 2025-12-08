// frontend/app/components/QuickActionButton.tsx
import React from "react";
import { Pressable, View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Props = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  primary?: boolean;
  onPress: () => void;
};

export default function QuickActionButton({
  label,
  icon,
  primary,
  onPress,
}: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        primary && styles.buttonPrimary,
        pressed && {
          transform: [{ scale: 0.96 }],
          opacity: 0.9,
        },
      ]}
    >
      <View style={styles.iconCircle}>
        <Ionicons
          name={icon}
          size={20}
          color={primary ? "#FEFCE8" : "#ffffffff"}
        />
      </View>
      <Text
        style={[styles.label, primary && styles.labelPrimary]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    flex: 1,
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5D8C8",
    paddingVertical: 10,
    paddingHorizontal: 10,
    alignItems: "center",
    gap: 6,
  },
  buttonPrimary: {
    backgroundColor: "#ffffffff",
    borderColor: "#8e444463",
  },
  iconCircle: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "#000000ff",
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    fontSize: 12,
    color: "#3B2F28",
    textAlign: "center",
  },
  labelPrimary: {
    fontWeight: "600",
    color: "#FEFCE8",
  },
});
