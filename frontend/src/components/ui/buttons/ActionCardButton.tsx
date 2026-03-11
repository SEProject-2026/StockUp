import React from "react";
import { Pressable, View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type BaseProps = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  subtitle?: string; //optional 
};

export default function ActionCardButton({
  label,
  icon,
  onPress,
  subtitle,
}: BaseProps) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.wrapper,
        pressed && {
          transform: [{ scale: 0.97 }],
          opacity: 0.9,
        },
      ]}
    >
      <View style={styles.card}>
        <View style={styles.iconRow}>
          <View style={styles.iconCircle}>
            <Ionicons name={icon} size={18} color="#FFFFFF" />
          </View>
        </View>

        <View style={styles.textBlock}>
          <Text style={styles.label}>{label}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginLeft: 10,
    padding: 4,
    borderRadius: 30,
    backgroundColor: "rgba(0,0,0,0.03)", // shadow effect
    shadowColor: "#000",
    shadowOpacity: 0.14,
    shadowOffset: { width: 0, height: 6 },
    shadowRadius: 12,
    elevation: 6,
  },
  card: {
    width: 110,
    height: 160,
    borderRadius: 26,
    paddingHorizontal: 10,
    paddingVertical: 12,
    justifyContent: "space-between",
    backgroundColor: "#FFFFFF",
  },
  iconRow: {
    alignItems: "center",
  },
  iconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#14365aff",
    alignItems: "center",
    justifyContent: "center",
  },
  textBlock: {
    alignItems: "stretch",
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
    textAlign: "center",
  },
  subtitle: {
    marginTop: 4,
    fontSize: 11,
    fontWeight: "600",
    color: "#14365aff",
    textAlign: "center",
  },
});
