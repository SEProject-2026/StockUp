import React from "react";
import { TouchableOpacity, Text, StyleSheet, StyleProp, ViewStyle } from "react-native";

type Props = {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
};

export default function PrimaryButton({ title, onPress, disabled, style }: Props) {
  return (
    <TouchableOpacity
      style={[styles.button, style, disabled && styles.buttonDisabled]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={styles.buttonText}>{title}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    alignSelf: "center",
    backgroundColor: "#0284C7",
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 999,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
