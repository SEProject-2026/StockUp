import React from "react";
import { Ionicons } from "@expo/vector-icons";
import ActionCardButton from "@/src/components/ui/buttons/ActionCardButton";

type Props = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
};

export default function QuickActionButton({ label, icon, onPress }: Props) {
  return (
    <ActionCardButton
      label={label}
      icon={icon}
      onPress={onPress}
      // בלי subtitle
    />
  );
}
