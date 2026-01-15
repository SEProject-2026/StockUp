import React from "react";
import { View, Text, StyleSheet, ViewStyle, TextStyle } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Props = {
  icon?: keyof typeof Ionicons.glyphMap;
  text: string;
  variant?: "info" | "warning" | "success";
  containerStyle?: ViewStyle;
  textStyle?: TextStyle;
};

const VARIANTS = {
  info: {
    bg: "#E0F2FE",
    color: "#0369A1",
    iconColor: "#0284C7",
    defaultIcon: "information-circle-outline" as const,
  },
  warning: {
    bg: "#FEF3C7",
    color: "#92400E",
    iconColor: "#D97706",
    defaultIcon: "warning-outline" as const,
  },
  success: {
    bg: "#DCFCE7",
    color: "#166534",
    iconColor: "#22C55E",
    defaultIcon: "checkmark-circle-outline" as const,
  },
};

export default function InfoBox({
  icon,
  text,
  variant = "info",
  containerStyle,
  textStyle,
}: Props) {
  const config = VARIANTS[variant];
  const iconName = icon ?? config.defaultIcon;

  return (
    <View
      style={[
        styles.infoBox,
        { backgroundColor: config.bg },
        containerStyle,
      ]}
    >
      <Ionicons name={iconName} size={18} color={config.iconColor} />
      <Text
        style={[
          styles.infoText,
          { color: config.color },
          textStyle,
        ]}
      >
        {text}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  infoBox: {
    flexDirection: "row-reverse",
    gap: 8,
    padding: 12,
    borderRadius: 12,
    alignItems: "center",
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    textAlign: "right",
  },
});
