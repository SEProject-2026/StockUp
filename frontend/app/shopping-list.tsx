import React, { useState, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  TextInput,
  TouchableOpacity,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

// Hooks & Components
import { useShoppingList } from "@/src/hooks/useShoppingList";
import { ShoppingItemRow } from "@/src/components/shopping/ShoppingItemRow";
import { QuickAddCard } from "@/src/components/shopping/QuickAddCard";
import { SuggestionsModal } from "@/src/components/shopping/SuggestionsModal";
import { ShoppingHero } from "@/src/components/shopping/ShoppingHero";
import { ActionButtons } from "@/src/components/shopping/ActionButtons";

// Layout Components
import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";

const BRAND = {
  BG: "#F4F4F4",
  MUTED: "#6B7280",
  BORDER: "#E5E7EB",
  TEXT: "#111827",
};

export default function ShoppingListScreen() {
  const insets = useSafeAreaInsets();
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);

  // כל הלוגיקה מגיעה מה-Hook המותאם אישית
  const {
    mode,
    setMode,
    items,
    filteredItems,
    suggestions,
    loading,
    picked,
    togglePick,
    query,
    setQuery,
    addItem,
    removeItem,
    finishShopping,
    syncing,
    existingNamesSet,
    updateQuantity,
  } = useShoppingList();

  const pickedCount = useMemo(
    () => Object.values(picked).filter(Boolean).length,
    [picked]
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ScreenHeader title="רשימת קניות" onBack={() => router.back()} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#0284C7" />
          <Text style={styles.loadingText}>טוען רשימת קניות...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient
          colors={["#E5F3FF", BRAND.BG]}
          style={StyleSheet.absoluteFill}
        />

        <ScreenHeader title="רשימת קניות" onBack={() => router.back()} />

        <FlatList
          data={filteredItems}
          keyExtractor={(item) => item.id}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{
            padding: 16,
            paddingBottom: 100 + insets.bottom,
          }}
          ListHeaderComponent={
            <>
              {/* כרטיס סיכום עליון */}
              <ShoppingHero
                mode={mode}
                itemsCount={items.length}
                pickedCount={pickedCount}
                suggestionsCount={suggestions.length}
              />

              {/* כפתורי פעולה (מצב קנייה, המלצות, סנכרון) */}
              <ActionButtons
                mode={mode}
                setMode={setMode}
                onOpenSuggestions={() => setSuggestionsOpen(true)}
                onSync={() => {}} // כאן תוכל לחבר את פונקציית הסנכרון מה-Hook
                syncing={syncing}
                onFinish={finishShopping}
              />

              {/* שורת חיפוש */}
              <View style={styles.searchCard}>
                <Ionicons name="search" size={18} color={BRAND.MUTED} />
                <TextInput
                  value={query}
                  onChangeText={setQuery}
                  placeholder="חיפוש בכל הרשימה..."
                  placeholderTextColor={BRAND.MUTED}
                  style={styles.searchInput}
                  textAlign="right"
                />
                {!!query && (
                  <TouchableOpacity onPress={() => setQuery("")}>
                    <Ionicons name="close-circle" size={18} color={BRAND.MUTED} />
                  </TouchableOpacity>
                )}
              </View>

              {/* כרטיס הוספה ידנית (רק במצב עריכה) */}
              {mode === "EDIT" && (
                <QuickAddCard
                  onAdd={(name, qty) => addItem(name, qty, "manual")}
                />
              )}

              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>
                  {mode === "EDIT" ? "פריטים לקנייה" : "הרשימה שלך"}
                </Text>
              </View>
            </>
          }
          renderItem={({ item }) => (
            <View style={styles.itemWrapper}>
              <ShoppingItemRow
                    item={item}
                    mode={mode}
                    isPicked={!!picked[item.id]}
                    onToggle={() => togglePick(item.id)}
                    onRemove={() => removeItem(item.id)}
                    onUpdateQty={(delta) => updateQuantity(item.id, delta)} 
                  />
            </View>
          )}
          ListEmptyComponent={
            <View style={styles.emptyCard}>
              <Ionicons name="basket-outline" size={24} color={BRAND.MUTED} />
              <Text style={styles.emptyTitle}>אין פריטים להצגה</Text>
            </View>
          }
        />

        {/* מודאל המלצות */}
        <SuggestionsModal
          open={suggestionsOpen}
          onClose={() => setSuggestionsOpen(false)}
          suggestions={suggestions}
          existingNamesSet={existingNamesSet}
          onAdd={(name) => {
            addItem(name, undefined, "suggestion");
            setSuggestionsOpen(false);
          }}
        />


        </SafeAreaView>
        <View style={[styles.bottomBar, { paddingBottom: 10 + insets.bottom }]}>
          <BottomNavBar activeTab="shopping-list" />
        </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F4F4F4",
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  loadingText: {
    marginTop: 8,
    color: "#6B7280",
    fontWeight: "700",
  },
  searchCard: {
    marginBottom: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 16,
    backgroundColor: "#FFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  searchInput: {
    flex: 1,
    color: "#111827",
    fontWeight: "700",
    fontSize: 14,
  },
  sectionHeader: {
    marginBottom: 10,
    marginTop: 5,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "900",
    color: "#111827",
    textAlign: "right",
  },
  itemWrapper: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#E8ECF3",
    overflow: "hidden",
  },
  emptyCard: {
    padding: 40,
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.5)",
    borderRadius: 20,
    borderStyle: "dashed",
    borderWidth: 1,
    borderColor: "#CCC",
  },
  emptyTitle: {
    marginTop: 10,
    color: "#6B7280",
    fontWeight: "700",
  },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255,255,255,0.9)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
});