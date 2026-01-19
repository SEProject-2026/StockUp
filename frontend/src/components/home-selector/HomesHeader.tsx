import React from "react";
import { View, Text, StyleSheet } from "react-native";

const TEXT = "#111827";

export default function HomesHeader({ title }: { title: string }) {
  return (
    <View style={styles.header}>
      <View style={{ width: 40 }} />
      <Text style={styles.headerTitle}>{title}</Text>
      <View style={{ width: 40 }} />
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 10,
  },
  headerTitle: {
    flex: 1,
    textAlign: "center",
    fontSize: 18,
    fontWeight: "800",
    color: TEXT,
  },
});
