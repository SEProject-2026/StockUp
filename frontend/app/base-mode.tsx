import React, { useState } from "react";
import { View, Text, StyleSheet, FlatList, TextInput, ActivityIndicator, KeyboardAvoidingView, Platform, TouchableOpacity } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";

import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import { useBaseMode } from "@/src/hooks/useBaseMode";
import { SummaryCard, LocationSection } from "@/src/components/baseMode/BaseModeComponents";
import AddBaseItemModal from "@/src/components/baseMode/AddBaseItemModal";

const BRAND = { BG: "#F4F4F4", TEXT: "#111827", MUTED: "#6B7280", PRIMARY: "#0284C7", BORDER: "#E5E7EB" };

export default function BaseModeScreen() {
  const insets = useSafeAreaInsets();
  const { state, actions } = useBaseMode();
  const [addOpen, setAddOpen] = useState(false);

  if (state.loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />
        <ScreenHeader title="מצב בסיס" onBack={() => router.back()} />
        <View style={styles.center}><ActivityIndicator size="large" color={BRAND.PRIMARY} /><Text style={styles.loadingText}>טוען מצב בסיס...</Text></View>
      </SafeAreaView>
    );
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />
        <ScreenHeader title="מצב בסיס" onBack={() => router.back()} />
        <AddBaseItemModal open={addOpen} onClose={() => setAddOpen(false)} onAdd={actions.addItem} />

        <FlatList
          data={state.groupedSections}
          keyExtractor={(s) => s.location}
          contentContainerStyle={[styles.content, { paddingBottom: 110 + insets.bottom }]}
          ListHeaderComponent={
            <>
              <View style={styles.heroCard}>
                <Text style={styles.heroTitle}>המלאי האידיאלי של הבית</Text>
                <Text style={styles.heroSubtitle}>כאן מגדירים מה תמיד אמור להיות בבית.</Text>
                <View style={styles.summaryRow}>
                  <SummaryCard title="פריטים" value={`${state.items.length}`} icon="list-outline" />
                  <SummaryCard title='סה"כ יעד' value={`${state.totalTarget}`} icon="stats-chart-outline" />
                </View>
              </View>
              <View style={styles.searchCard}>
                <Ionicons name="search" size={18} color={BRAND.MUTED} />
                <TextInput value={state.query} onChangeText={actions.setQuery} placeholder="חיפוש בכל הרשימה..." style={styles.searchInput} textAlign="right" />
                {!!state.query && <TouchableOpacity onPress={() => actions.setQuery("")}><Ionicons name="close-circle" size={18} color={BRAND.MUTED} /></TouchableOpacity>}
              </View>
            </>
          }
          renderItem={({ item }) => (
            <LocationSection section={item} busyIds={state.busyIds} onIncrease={(id: any) => actions.bumpQty(id, 1)} onDecrease={(id: any) => actions.bumpQty(id, -1)} onRemove={actions.removeItem} />
          )}
          ItemSeparatorComponent={() => <View style={{ height: 14 }} />}
        />
        <View style={[styles.bottomBar, { paddingBottom: 16 + insets.bottom }]}><PrimaryButton title="הוסף פריט" onPress={() => setAddOpen(true)} /></View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: BRAND.BG },
  content: { padding: 16 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  loadingText: { marginTop: 8, color: BRAND.MUTED, fontWeight: "700", fontSize: 13 },
  heroCard: { backgroundColor: "rgba(255,255,255,0.92)", borderRadius: 22, padding: 15, borderWidth: 1, borderColor: "#E8ECF3", marginBottom: 12 },
  heroTitle: { fontSize: 18, fontWeight: "900", color: BRAND.TEXT, textAlign: "right" },
  heroSubtitle: { marginTop: 6, color: BRAND.MUTED, fontWeight: "700", fontSize: 12.5, textAlign: "right" },
  summaryRow: { flexDirection: "row-reverse", gap: 10, marginTop: 12 },
  searchCard: { marginBottom: 14, flexDirection: "row-reverse", alignItems: "center", gap: 8, paddingHorizontal: 12, paddingVertical: 11, borderRadius: 16, backgroundColor: "rgba(255,255,255,0.96)", borderWidth: 1, borderColor: BRAND.BORDER },
  searchInput: { flex: 1, color: BRAND.TEXT, fontWeight: "700", fontSize: 13 },
  bottomBar: { position: "absolute", left: 0, right: 0, bottom: 0, padding: 16, backgroundColor: "rgba(244,244,244,0.95)", borderTopWidth: 1, borderTopColor: "#E5E7EB" },
});