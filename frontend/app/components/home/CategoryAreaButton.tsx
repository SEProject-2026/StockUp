import React from "react";
import { Ionicons } from "@expo/vector-icons";
import ActionCardButton from "./ActionCardButton";

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
  return (
    <ActionCardButton
      label={label}
      icon={icon}
      onPress={onPress}
      subtitle={`${value} פריטים`}
    />
  );
}
