import React from "react";
import { Ionicons } from "@expo/vector-icons";
import ActionCardButton from "../../components/ui/buttons/ActionCardButton";

type Props = {
  label: "מקרר" | "מקפיא" | "מזווה" | "ציוד ניקוי" | "אחר";
  value: number;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
};

export default function locationAreaButton({
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
