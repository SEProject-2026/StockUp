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

export default function ShoppingListScreen() {
  const insets = useSafeAreaInsets();
  const [addOpen, setAddOpen] = useState(false);
  const { homeId, listId, listName } = useLocalSearchParams<{ homeId: string; listId: string; listName: string }>();

  const {
    mode, items, filteredItems, loading, picked, query, setQuery,
    addItem, removeItem, finishShopping, updateQuantity, enterShoppingMode, modeSubmitting, togglePick
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
                      onToggle={() => togglePick(it.id)} onIncrease={() => updateQuantity(it.id, 1)} 
                      onDecrease={() => updateQuantity(it.id, -1)} onRemove={() => removeItem(it.id)} 
                    />
                    {i < section.items.length - 1 && <View style={styles.separator} />}
                  </View>
                ))}
              </View>
            </View>
          )}
        />

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
  );}