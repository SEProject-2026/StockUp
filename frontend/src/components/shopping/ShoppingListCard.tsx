import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert, Animated } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Swipeable } from "react-native-gesture-handler";

const BRAND = {
  TEXT: "#111827",
  MUTED: "#6B7280",
  BORDER: "#E5E7EB",
  PRIMARY: "#0284C7",
  CARD: "#FFFFFF",
  SUCCESS: "#10B981",
  DANGER: "#DC2626",
};

export const ShoppingListCard = React.memo(({ item, onPress, onDelete }: any) => {
  const progress = item.itemsCount > 0 ? Math.round((item.pickedCount / item.itemsCount) * 100) : 0;

  // פונקציה שמייצרת את הכפתור שמופיע מתחת לכרטיס בזמן גרירה
  const renderLeftActions = (progress: any, dragX: any) => {
    const trans = dragX.interpolate({
      inputRange: [0, 50, 100],
      outputRange: [-20, 0, 10],
    });

    return (
      <TouchableOpacity 
        style={styles.deleteAction} 
        onPress={() => {
            Alert.alert("מחיקה", `למחוק את ${item.name}?`, [
                { text: "ביטול", style: "cancel" },
                { text: "מחק", style: "destructive", onPress: () => onDelete(item.id) }
            ]);
        }}
      >
        <Animated.View style={[styles.actionIcon, { transform: [{ translateX: trans }] }]}>
          <Ionicons name="trash" size={24} color="#fff" />
        </Animated.View>
      </TouchableOpacity>
    );
  };

  return (
    <Swipeable
      renderLeftActions={renderLeftActions} // גרירה מימין לשמאל (בשפת RTL זה יוצא הפוך, אז Left עובד טוב)
      friction={2}
      leftThreshold={40}
    >
      <TouchableOpacity activeOpacity={1} style={styles.card} onPress={() => onPress(item)}>
        <View style={styles.cardTopRow}>
          <View style={styles.arrowWrap}>
            <Ionicons name="chevron-back" size={20} color={BRAND.MUTED} />
          </View>
          <View style={styles.cardTitleWrap}>
            <Text style={styles.cardTitle}>{item.name}</Text>
            <Text style={styles.cardSubtitle}>{item.updatedAt}</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statPill}>
            <Ionicons name="list-outline" size={14} color={BRAND.PRIMARY} />
            <Text style={styles.statText}>{item.itemsCount} פריטים</Text>
          </View>
          <View style={styles.statPill}>
            <Ionicons name="checkmark-done-outline" size={14} color={BRAND.SUCCESS} />
            <Text style={styles.statText}>{item.pickedCount} סומנו</Text>
          </View>
          <View style={styles.statPill}>
            <Ionicons name="pie-chart-outline" size={14} color={BRAND.TEXT} />
            <Text style={styles.statText}>{progress}% הושלם</Text>
          </View>
        </View>
      </TouchableOpacity>
    </Swipeable>
  );
});

const styles = StyleSheet.create({
  card: { 
    backgroundColor: BRAND.CARD, 
    borderRadius: 20, 
    padding: 14, 
    marginBottom: 12, 
    borderWidth: 1, 
    borderColor: BRAND.BORDER,
  },
  deleteAction: {
    backgroundColor: BRAND.DANGER,
    justifyContent: "center",
    alignItems: "flex-start",
    width: 90,
    height: "83%", // מתאים לגובה ה-Card פחות ה-Margin
    borderRadius: 20,
    marginBottom: 12,
  },
  actionIcon: {
    paddingHorizontal: 30,
  },
  cardTopRow: { flexDirection: "row-reverse", alignItems: "center", marginBottom: 12 },
  arrowWrap: { marginLeft: 10 },
  cardTitleWrap: { flex: 1 },
  cardTitle: { textAlign: "right", color: BRAND.TEXT, fontSize: 16, fontWeight: "900" },
  cardSubtitle: { textAlign: "right", color: BRAND.MUTED, marginTop: 3, fontSize: 12, fontWeight: "600" },
  statsRow: { flexDirection: "row-reverse", flexWrap: "wrap", gap: 8 },
  statPill: { flexDirection: "row-reverse", alignItems: "center", gap: 6, backgroundColor: "#F8FAFC", borderRadius: 999, paddingVertical: 8, paddingHorizontal: 10, borderWidth: 1, borderColor: "#E8EEF5" },
  statText: { color: BRAND.TEXT, fontSize: 12, fontWeight: "800" },
});