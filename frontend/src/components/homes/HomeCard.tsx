import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Home = {
  id: string;
  name: string;
  pendingRequestsCount: number;
  adminId: string;
  expirationRange: number;
};

const BRAND_PRIMARY = "#0284C7";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";
const CARD = "#FFFFFF";
const SOFT_BLUE = "rgba(2,132,199,0.10)";
const SOFT_ORANGE = "rgba(245,158,11,0.12)";

type Props = {
  home: Home;
  onPress: () => void;
};

export default function HomeCard({ home, onPress }: Props) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85} style={styles.card}>
      <View style={styles.cardTopRow}>
        <View style={styles.gridIcon}>
          <Ionicons name="home-outline" size={22} color={BRAND_PRIMARY} />
        </View>

        {home.pendingRequestsCount > 0 ? (
          <View style={styles.pendingBadge}>
            <Ionicons name="mail-unread-outline" size={13} color="#B45309" />
            <Text style={styles.pendingText} numberOfLines={1}>
              {home.pendingRequestsCount} ממתינות
            </Text>
          </View>
        ) : null}
      </View>

      <View style={styles.content}>
        <Text style={styles.homeName} numberOfLines={2} ellipsizeMode="tail">
          {home.name}
        </Text>
      </View>

      <View style={styles.cardBottomRow}>
        <Ionicons name="chevron-back" size={18} color={MUTED} />
      </View>
    </TouchableOpacity>
  );
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
    minHeight: 44,
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

  pendingBadge: {
    maxWidth: "68%",
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: SOFT_ORANGE,
    borderWidth: 1,
    borderColor: "rgba(245,158,11,0.25)",
  },

  pendingText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#92400E",
    textAlign: "right",
  },

  content: {
    flex: 1,
    justifyContent: "center",
    marginTop: 8,
  },

  homeName: {
    fontSize: 16,
    fontWeight: "800",
    color: TEXT,
    textAlign: "right",
    lineHeight: 22,
  },

  metaColumn: {
    marginTop: 12,
    alignItems: "flex-end",
    gap: 8,
  },

  metaPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: SOFT_BLUE,
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.16)",
    alignSelf: "flex-end",
  },

  metaText: {
    fontSize: 12,
    fontWeight: "800",
    color: TEXT,
    textAlign: "right",
  },

  cardBottomRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "flex-start",
    marginTop: 10,
  },
});