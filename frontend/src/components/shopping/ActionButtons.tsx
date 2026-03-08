import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export const ActionButtons = ({ mode, setMode, onOpenSuggestions, onSync, syncing, onFinish, finishing }: any) => {
  if (mode === "EDIT") {
    return (
      <View style={styles.actionsWrap}>
        <TouchableOpacity onPress={() => setMode("SHOPPING")} style={styles.primaryPill}>
          <Ionicons name="cart-outline" size={16} color="#fff" />
          <Text style={styles.pillText}>מצב קנייה</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={onOpenSuggestions} style={styles.secondaryPill}>
          <Ionicons name="sparkles-outline" size={16} color="#111" />
          <Text style={styles.pillTextDark}>המלצות</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={onSync} disabled={syncing} style={styles.secondaryPill}>
          {syncing ? <ActivityIndicator size="small" color="#0284C7" /> : (
            <>
              <Ionicons name="refresh-outline" size={16} color="#111" />
              <Text style={styles.pillTextDark}>סנכרון</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.actionsWrap}>
      <TouchableOpacity onPress={onFinish} disabled={finishing} style={styles.finishPill}>
        <Text style={styles.pillText}>סיום קנייה</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => setMode("EDIT")} style={styles.secondaryPill}>
        <Text style={styles.pillTextDark}>ביטול</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  actionsWrap: { flexDirection: "row-reverse", gap: 8, marginBottom: 12, flexWrap: "wrap" },
  primaryPill: { flexDirection: "row-reverse", alignItems: "center", gap: 6, paddingHorizontal: 15, paddingVertical: 10, borderRadius: 25, backgroundColor: "#0284C7" },
  secondaryPill: { flexDirection: "row-reverse", alignItems: "center", gap: 6, paddingHorizontal: 15, paddingVertical: 10, borderRadius: 25, backgroundColor: "#FFF", borderWidth: 1, borderColor: "#DDD" },
  finishPill: { backgroundColor: "#16A34A", paddingHorizontal: 20, paddingVertical: 10, borderRadius: 25 },
  pillText: { color: "#FFF", fontWeight: "800", fontSize: 13 },
  pillTextDark: { color: "#111", fontWeight: "800", fontSize: 13 }
});