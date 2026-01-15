import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BRAND, PrimaryButtonCompat } from "./review.shared";

export default function ReviewFooter(props: {
  saving: boolean;
  disabled: boolean;
  onConfirm: () => void;
}) {
  const { saving, disabled, onConfirm } = props;

  return (
    <View style={styles.footer}>
      <PrimaryButtonCompat
        title={saving ? "מוסיף למלאי..." : "אישור והוספה למלאי"}
        onPress={onConfirm}
        leftIcon={<Ionicons name="checkmark-circle-outline" size={20} color={BRAND.TEXT} />}
        disabled={disabled}
      />
      <Text style={styles.footerHint}>לפני שתמשיכו: מומלץ למקם את המוצרים בהתאם לאזורי הבית </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  footer: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 14,
    backgroundColor: "rgba(245,246,248,0.96)",
    borderTopWidth: 1,
    borderTopColor: BRAND.BORDER,
  },
  footerHint: { marginTop: 8, fontSize: 11, color: BRAND.MUTED, textAlign: "right" },
});
