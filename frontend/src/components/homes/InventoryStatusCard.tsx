import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_RED = "#c43131ff";

export type Stats = {
  total: number;
  fridge: number;
  freezer: number;
  pantry: number;
  expiringSoon: number;
};

type Props = {
  stats: Stats;
};

export default function InventoryStatusCard({ stats }: Props) {
  return (
    <View style={styles.statusWrapper}>
      <LinearGradient
        colors={["#ffffffff", "#D7F0FF"]}
        start={{ x: 0.5, y: 0.5 }}
        end={{ x: 0.5, y: 0 }}
        style={styles.statusCard}
      >
        <View style={styles.statusHeaderRow}>
          <View style={styles.statusTitleBadge}>
            <Text style={styles.statusTitleText}>סטטוס מלאי</Text>
          </View>
          <Ionicons name="stats-chart" size={18} color="#111827" />
        </View>

        <View style={styles.statusStatsRow}>
          <View style={styles.statusColumn}>
            <Text style={styles.statusLabel}>סה״כ פריטים</Text>
            <Text style={styles.statusValue}>{stats.total}</Text>
          </View>
          <View style={styles.statusDivider} />
          <View style={styles.statusColumn}>
            <Text style={styles.statusLabel}>תוקף קרוב</Text>
            <Text style={[styles.statusValue, styles.statusValueAlert]}>
              {stats.expiringSoon}
            </Text>
          </View>
        </View>

        <Text style={styles.statusHintText}>
          לחץ על אחד האזורים למטה כדי לראות את הפריטים הרלוונטיים.
        </Text>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  statusWrapper: {
    borderRadius: 26,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 3,
  },
  statusCard: {
    borderRadius: 26,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  statusHeaderRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  statusTitleBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#FFFFFFCC",
  },
  statusTitleText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111827",
    textAlign: "center",
  },
  statusStatsRow: {
    flexDirection: "row-reverse",
    alignItems: "stretch",
    marginBottom: 8,
  },
  statusColumn: {
    flex: 1,
    alignItems: "flex-end",
    paddingHorizontal: 6,
  },
  statusLabel: {
    fontSize: 11,
    color: "#4B5563",
    marginBottom: 4,
    textAlign: "right",
  },
  statusValue: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111827",
  },
  statusValueAlert: {
    color: BRAND_RED,
  },
  statusDivider: {
    width: 1,
    backgroundColor: "#E5E7EB",
  },
  statusHintText: {
    marginTop: 4,
    fontSize: 11,
    color: "#4B5563",
    textAlign: "right",
  },
});
