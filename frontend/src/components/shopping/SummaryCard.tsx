import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND = {
  CARD: "#FFFFFF",
  BORDER: "#E5E7EB",
  TEXT: "#111827",
  MUTED: "#6B7280",
  PRIMARY: "#0284C7",
  PRIMARY_SOFT: "#E5F3FF",
};

export default function SummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: any;
}) {
  return (
    <View style={styles.summaryCard}>
      <View style={styles.summaryIconWrap}>
        <Ionicons name={icon} size={17} color={BRAND.PRIMARY} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.summaryTitle}>{title}</Text>
        <Text style={styles.summaryValue}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  summaryCard: {
    flex: 1,
    backgroundColor: BRAND.CARD,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    padding: 11,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },
  summaryIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: BRAND.PRIMARY_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },
  summaryTitle: {
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 11,
    textAlign: "right",
  },
  summaryValue: {
    marginTop: 2,
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 16,
    textAlign: "right",
  },
});