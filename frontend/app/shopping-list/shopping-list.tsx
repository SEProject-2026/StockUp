import React, { useCallback, useMemo, useState } from "react";
import { View, FlatList, ActivityIndicator, Alert, StyleSheet, Text } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams, useFocusEffect } from "expo-router";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";
import { getHomeShoppingLists, createShoppingList, deleteShoppingList } from "@/src/api/shoppingLists";

import { ShoppingListCard } from "@/src/components/shopping/ShoppingListCard";
import { ShoppingListsHeader } from "@/src/components/shopping/ShoppingListsHeader";
import { Gesture, GestureHandlerRootView } from "react-native-gesture-handler";

const BRAND = { BG: "#F4F4F4", PRIMARY: "#0284C7", PRIMARY_SOFT: "#E5F3FF", TEXT: "#111827", MUTED: "#6B7280" };

export default function ShoppingListsScreen() {
  const insets = useSafeAreaInsets();
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newListName, setNewListName] = useState("");
  const [lists, setLists] = useState<any[]>([]);

  const loadLists = useCallback(async () => {
    if (!homeId) return setLoading(false);
    try {
      setLoading(true);
      const data = await getHomeShoppingLists(homeId);
      setLists(data.map(dto => ({
        id: dto.id,
        name: dto.name,
        itemsCount: dto.items.length,
        pickedCount: dto.items.filter((i: any) => i.is_bought).length,
        updatedAt: "עודכן לאחרונה" 
      })));
    } catch (e) {
      Alert.alert("שגיאה", "טעינת הרשימות נכשלה");
    } finally { setLoading(false); }
  }, [homeId]);

  useFocusEffect(useCallback(() => { loadLists(); }, [loadLists]));

  const handleCreate = async () => {
    if (!newListName.trim() || !homeId) return;
    try {
      setCreating(true);
      await createShoppingList({ home_id: homeId, name: newListName.trim() });
      setNewListName("");
      loadLists();
    } catch (e) {
      Alert.alert("שגיאה", "נכשל");
    } finally { setCreating(false); }
  };
  const handleDeleteList = async (listId: string) => {
    try {
      await deleteShoppingList(listId); 
      setLists(prev => prev.filter(l => l.id !== listId)); 
    } catch (e) {
      Alert.alert("שגיאה", "לא הצלחנו למחוק את הרשימה");
    }
  };


  return (
  <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaView style={{ flex: 1, backgroundColor: BRAND.BG }}>
      <LinearGradient colors={[BRAND.PRIMARY_SOFT, BRAND.BG]} style={StyleSheet.absoluteFill} />
      <ScreenHeader title="רשימות קניות" onBack={() => router.back()} />

      <FlatList
          data={lists}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ padding: 16, paddingBottom: 100 + insets.bottom }}
          ListHeaderComponent={
            <ShoppingListsHeader 
              newListName={newListName} setNewListName={setNewListName}
              onCreate={handleCreate} creating={creating} listsCount={lists.length}
            />
          }
          renderItem={({ item }) => (
            <ShoppingListCard 
              item={item} 
              onDelete={handleDeleteList} 
              onPress={(l: any) => router.push({
                pathname: "/shopping-list/[listId]",
                params: { homeId, listId: l.id, listName: l.name }
              })} 
            />
          )}
        />

      <View style={bottomStyles.bottomBarContainer}>
        <View style={{ paddingBottom: 10 + insets.bottom }}>
          <BottomNavBar activeTab="shopping-list" />
        </View>
      </View>
    </SafeAreaView>
  </GestureHandlerRootView>
  );
}

const bottomStyles = StyleSheet.create({
  bottomBarContainer: { position: "absolute", bottom: 0, left: 0, right: 0, backgroundColor: "rgba(255,255,255,0.94)", borderTopWidth: 1, borderTopColor: "#E5E7EB" }
});