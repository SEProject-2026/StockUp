import React from "react";
import { Text, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

const BRAND_BLUE_SOFT = "#F0FAFF";

type Props = {
  label: string;
};

export default function SideTitleCard({ label }: Props) {
  return (
    <LinearGradient
      colors={["#ffffffff", "#D7F0FF"]}
      start={{ x: 0.5, y: 1.5 }}
      end={{ x: 0.5, y: 0 }}
      style={styles.sideTitleCard}
    >
      <Text style={styles.sideTitleCardText}>{label}</Text>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  sideTitleCard: {
    width: 110,
    height: 160,
    borderRadius: 26,
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 10,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 3,
    backgroundColor: BRAND_BLUE_SOFT,
  },
  sideTitleCardText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111827",
    textAlign: "center",
    lineHeight: 22,
  },
});
