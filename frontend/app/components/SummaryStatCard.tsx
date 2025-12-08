// app/components/SummaryStatCard.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type SummaryStatCardProps = {
  label: string;
  value: number;
  icon: keyof typeof Ionicons.glyphMap;
  accent?: boolean;
  styles: any; // מקבל את ה־styles מהמסך הראשי
};

export function SummaryStatCard({
  label,
  value,
  icon,
  accent,
  styles,
}: SummaryStatCardProps) {
  return (
    <View style={[styles.heroStat, accent && styles.heroStatAccent]}>
      <View style={styles.heroStatIconCircle}>
        <Ionicons name={icon} size={16} color={accent ? "#BFDBFE" : "#3B82F6"} />
      </View>

      <Text style={styles.heroStatValue}>{value}</Text>
      <Text style={styles.heroStatLabel}>{label}</Text>
    </View>
  );
}
