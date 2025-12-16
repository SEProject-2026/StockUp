import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Home = {
  id: string;
  name: string;
  membersCount: number;
  updatedAt: string; // ISO
};

const BRAND_PRIMARY = "#0284C7";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";
const CARD = "#FFFFFF";

type Props = {
  home: Home;
  onPress: () => void;
};

export default function HomeCard({ home, onPress }: Props) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85} style={styles.card}>
      {/* Top row: icon + updated */}
      <View style={styles.cardTopRow}>
        <View style={styles.gridIcon}>
          <Ionicons name="home-outline" size={22} color={BRAND_PRIMARY} />
        </View>

        <View style={styles.updatedPill}>
          <Ionicons name="time" size={14} color={MUTED} />
          <Text style={styles.updatedText} numberOfLines={1}>
            {formatRelativeDate(home.updatedAt)}
          </Text>
        </View>
      </View>

      {/* Name */}
      <Text style={styles.homeName} numberOfLines={2} ellipsizeMode="tail">
        {home.name}
      </Text>

      {/* Bottom row */}
      <View style={styles.cardBottomRow}>
        <View style={styles.metaPill}>
          <Ionicons name="person-outline" size={14} color={BRAND_PRIMARY} />
          <Text style={styles.metaText} numberOfLines={1}>
            {home.membersCount} {home.membersCount === 1 ? "אדם" : "אנשים"}
          </Text>
        </View>

        <Ionicons name="chevron-back" size={18} color={MUTED} />
      </View>
    </TouchableOpacity>
  );
}

function formatRelativeDate(iso: string) {
  const d = new Date(iso);
  const diffMs = Date.now() - d.getTime();

  if (diffMs < 0) return "עוד רגע";

  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "עכשיו";
  if (minutes < 60) return `${minutes} דק׳`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} ש׳`;

  const days = Math.floor(hours / 24);
  return days === 1 ? "אתמול" : `${days} ימים`;
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 18,
    padding: 14,
    flexDirection: "column",
    alignItems: "stretch",
    justifyContent: "space-between",
    aspectRatio: 1,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
  },

  cardTopRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
  },

  gridIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: "rgba(2,132,199,0.12)",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "flex-end",
  },

  updatedPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: BORDER,
    maxWidth: "70%",
  },
  updatedText: {
    fontSize: 11,
    fontWeight: "700",
    color: MUTED,
    textAlign: "right",
  },

  homeName: {
    marginTop: 10,
    fontSize: 15,
    fontWeight: "800",
    color: TEXT,
    textAlign: "right",
  },

  cardBottomRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
  },

  metaPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: "rgba(2,132,199,0.10)",
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.16)",
  },
  metaText: {
    fontSize: 12,
    fontWeight: "800",
    color: TEXT,
    textAlign: "right",
  },
});
