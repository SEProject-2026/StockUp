import React, { useMemo, useState } from "react";
import { View, Text, FlatList, ActivityIndicator, KeyboardAvoidingView, Platform, TouchableOpacity, Alert, StyleSheet } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { useShoppingList, type ShoppingItem, type LocationKey } from "@/src/hooks/useShoppingList";
import { LOCATIONS, locationLabel, locationIcon } from "@/src/hooks/useBaseMode";
import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";

import { styles, BRAND, type SectionLocation } from "@/src/components/shopping/styles";
import { ShoppingItemRow } from "@/src/components/shopping/ShoppingItemRow";
import { ShoppingHeader } from "@/src/components/shopping/ShoppingHeader";
import { AddShoppingItemModal } from "@/src/components/shopping/AddShoppingItemModal";
import { SuggestionsModal } from "@/src/components/shopping/SuggestionsModal";

const fabStyles = StyleSheet.create({
  container: {
    position: "absolute",
    right: 20,
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#F59E0B",
    alignItems: "center",
    justifyContent: "center",
    elevation: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    zIndex: 999,
  },
  badge: {
    position: "absolute",
    top: -2,
    left: -2,
    backgroundColor: "#EF4444",
    minWidth: 24,
    height: 24,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
    borderWidth: 2,
    borderColor: "#fff",
    zIndex: 1000,
  },
  badgeText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "900",
  }
});

export default function ShoppingListScreen() {
  const insets = useSafeAreaInsets();
  const [addOpen, setAddOpen] = useState(false);
  const { homeId, listId, listName } = useLocalSearchParams<{ homeId: string; listId: string; listName: string }>();

  const {
    mode, items, filteredItems, loading, picked, query, setQuery,
    addItem, removeItem, finishShopping, updateQuantity, enterShoppingMode, modeSubmitting, togglePick, 
    suggestions, dismissSuggestion, suggestionsModalOpen, setSuggestionsModalOpen
  } = useShoppingList({ homeId: homeId ?? "", listId: listId ?? "" });

  const pickedCount = useMemo(() => Object.values(picked).filter(Boolean).length, [picked]);

  const groupedSections = useMemo(() => {
    const groups = new Map<SectionLocation, ShoppingItem[]>();
    
    filteredItems.forEach((it) => {
      const loc = (it.location as SectionLocation) || "UNSORTED";
      if (!groups.has(loc)) groups.set(loc, []);
      groups.get(loc)!.push(it);
    });

    const sections = (LOCATIONS as LocationKey[])
      .filter(l => groups.has(l as SectionLocation))
      .map(l => ({
        location: l as SectionLocation,
        title: locationLabel(l as any),
        items: groups.get(l as SectionLocation)!
      }));

    if (groups.has("UNSORTED")) {
      sections.push({ location: "UNSORTED", title: "ללא מיקום", items: groups.get("UNSORTED")! });
    }
    return sections;
  }, [filteredItems]);

  if (loading) return (
    <SafeAreaView style={styles.safeArea}>
      <ScreenHeader title={listName || "טוען..."} onBack={() => router.back()} />
      <View style={styles.center}><ActivityIndicator size="large" color={BRAND.PRIMARY} /></View>
    </SafeAreaView>
  );

return (
    <View style={{ flex: 1 }}>
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />
        <ScreenHeader title={listName || "רשימת קניות"} onBack={() => router.back()} />
        
        <FlatList
          data={groupedSections}
          keyExtractor={s => s.location}
          contentContainerStyle={{ padding: 16, paddingBottom: 100 + insets.bottom }} // צמצמתי מרווח תחתון
          ListHeaderComponent={
            <ShoppingHeader 
              isShoppingMode={mode === "SHOPPING"} totalCount={items.length} pickedCount={pickedCount}
              query={query} setQuery={setQuery} modeSubmitting={modeSubmitting}
              onToggleMode={() => mode === "SHOPPING" ? finishShopping(false) : enterShoppingMode()}
            />
          }
          renderItem={({ item: section }) => (
            <View style={styles.sectionContainer}>
              <View style={styles.sectionBlock}>
                <View style={styles.locationHeader}>
                  <View style={styles.locationHeaderLine} />
                  <View style={styles.locationHeaderChip}>
                    <Ionicons 
                      name={(section.location === "UNSORTED" ? "albums-outline" : locationIcon(section.location as any)) as any} 
                      size={14} color={BRAND.PRIMARY} 
                    />
                    <Text style={styles.locationHeaderText}>{section.title}</Text>
                  </View>
                </View>
              </View>
              <View style={styles.notebookCard}>
                {section.items.map((it, i) => (
                  <View key={it.id}>
                    <ShoppingItemRow 
                      item={it} mode={mode} isPicked={!!picked[it.id]} 
                      onToggle={() => togglePick(it.id)} 
                      onIncrease={() => updateQuantity(it.id, 1)} 
                      onDecrease={() => updateQuantity(it.id, -1)} 
                      onRemove={() => removeItem(it.id)} 
                    />
                    {i < section.items.length - 1 && <View style={styles.separator} />}
                  </View>
                ))}
              </View>
            </View>
          )}
        />

        {/* Suggestions Modal */}
        <SuggestionsModal 
          open={suggestionsModalOpen} 
          onClose={() => setSuggestionsModalOpen(false)} 
          suggestions={suggestions}
          onAdd={(name) => addItem(name, 1, "suggestion", "OTHER")}
          onDismiss={dismissSuggestion}
        />

        {/* Floating Suggestions Button */}
        {suggestions.length > 0 && (
          <TouchableOpacity 
            style={[
              fabStyles.container, 
              { bottom: 85 + insets.bottom } // Above bottom actions
            ]}
            onPress={() => setSuggestionsModalOpen(true)}
          >
            <View style={fabStyles.badge}>
              <Text style={fabStyles.badgeText}>{suggestions.length}</Text>
            </View>
            <Ionicons name="sparkles" size={24} color="#fff" />
          </TouchableOpacity>
        )}

        {/* הכפתור הדינמי בתחתית המסך */}
        <View style={[styles.bottomActions, { paddingBottom: 16 + insets.bottom }]}>
          {mode === "SHOPPING" ? (
            <TouchableOpacity 
              style={[styles.primaryBottomBtnFull, { backgroundColor: BRAND.SUCCESS }]} 
              onPress={() => {
                Alert.alert(
                  "סיום קנייה", 
                  "האם לסיים את הקנייה ולמחוק את כל הפריטים שסימנת?", 
                  [
                    { text: "ביטול", style: "cancel" },
                    { text: "מחק וסיים", style: "destructive", onPress: () => finishShopping(true) }
                  ]
                );
              }}
            >
              <Ionicons name="checkmark-circle-outline" size={22} color="#fff" />
              <Text style={styles.primaryBottomBtnText}>סיום קנייה ומחיקת פריטים</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity 
              style={styles.primaryBottomBtnFull} 
              onPress={() => setAddOpen(true)}
            >
              <Ionicons name="add" size={22} color="#fff" />
              <Text style={styles.primaryBottomBtnText}>הוסף פריט חדש</Text>
            </TouchableOpacity>
          )}
        </View>

        <AddShoppingItemModal open={addOpen} onClose={() => setAddOpen(false)} onAdd={(p) => addItem(p.name, p.qty, "manual", p.location)} />
        <View style={[styles.bottomBar, { paddingBottom: 10 + insets.bottom }]}><BottomNavBar activeTab="shopping-list" /></View>
      </SafeAreaView>
    </View>
  );
}