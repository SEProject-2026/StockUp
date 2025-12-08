// app/components/AreaShortcut.tsx
import React from "react";
import { Pressable, View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type AreaShortcutProps = {
  label: string;
  value: number;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  styles: any;
};

export function AreaShortcut({
  label,
  value,
  icon,
  onPress,
  styles,
}: AreaShortcutProps) {
  return (
    <Pressable style={styles.heroArea} onPress={onPress}>
      <View
        style={{
          flexDirection: "row-reverse",
          alignItems: "center",
          gap: 4,
        }}
      >
        <Ionicons name={icon} size={14} color="#2563EB" />
        <Text style={styles.heroAreaLabel}>{label}</Text>
      </View>
      <Text style={styles.heroAreaValue}>{value}</Text>
    </Pressable>
  );
}
