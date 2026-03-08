import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export const ShoppingHero = ({ mode, itemsCount, pickedCount, suggestionsCount, onSync, syncing }: any) => {
  return (
    <View style={styles.heroCard}>
      <Text style={styles.heroTitle}>{mode === "EDIT" ? "הקניות של הבית" : "מצב קנייה פעיל"}</Text>
      
      <View style={styles.summaryRow}>
        <View style={styles.summaryCard}>
          <Ionicons name="list-outline" size={17} color="#0284C7" />
          <View>
            <Text style={styles.sumTitle}>פריטים</Text>
            <Text style={styles.sumVal}>{itemsCount}</Text>
          </View>
        </View>
        <View style={styles.summaryCard}>
          <Ionicons name={mode === "EDIT" ? "sparkles-outline" : "checkmark-done-outline"} size={17} color="#0284C7" />
          <View>
            <Text style={styles.sumTitle}>{mode === "EDIT" ? "המלצות" : "סומנו"}</Text>
            <Text style={styles.sumVal}>{mode === "EDIT" ? suggestionsCount : pickedCount}</Text>
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  heroCard: { backgroundColor: "rgba(255,255,255,0.9)", borderRadius: 22, padding: 15, marginBottom: 12, borderWidth: 1, borderColor: "#E8ECF3" },
  heroTitle: { fontSize: 18, fontWeight: "900", textAlign: "right" },
  summaryRow: { flexDirection: "row-reverse", gap: 10, marginTop: 12 },
  summaryCard: { flex: 1, backgroundColor: "#FFF", borderRadius: 16, padding: 10, flexDirection: "row-reverse", alignItems: "center", gap: 8, borderWidth: 1, borderColor: "#EEE" },
  sumTitle: { fontSize: 11, color: "#6B7280", fontWeight: "800", textAlign: "right" },
  sumVal: { fontSize: 16, fontWeight: "900", textAlign: "right" }
});