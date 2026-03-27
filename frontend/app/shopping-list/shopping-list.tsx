import React, { useCallback, useEffect, useState } from "react";
import { View, FlatList, ActivityIndicator, Alert, StyleSheet, Text } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";
import { 
  getHomeShoppingLists, 
  createShoppingList, 
  deleteShoppingList 
} from "@/src/api/shoppingLists";

import { ShoppingListCard } from "@/src/components/shopping/ShoppingListCard";
import { ShoppingListsHeader } from "@/src/components/shopping/ShoppingListsHeader";
import { supabase } from "./supabase";
const BRAND = { 
  BG: "#F4F4F4", 
  PRIMARY: "#0284C7", 
  PRIMARY_SOFT: "#E5F3FF", 
  TEXT: "#111827", 
  MUTED: "#6B7280" 
};

export default function ShoppingListsScreen() {
  const insets = useSafeAreaInsets();
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newListName, setNewListName] = useState("");
  const [lists, setLists] = useState<any[]>([]);

  // --- פונקציית טעינת הנתונים ---
  const loadLists = useCallback(async () => {
    if (!homeId) return;
    try {
      // בטעינה הראשונה בלבד נציג אינדיקטור מרכזי
      const data = await getHomeShoppingLists(homeId);
      
      const formattedLists = data.map(dto => ({
        id: dto.id,
        name: dto.name,
        itemsCount: dto.items?.length || 0,
        pickedCount: dto.items?.filter((i: any) => i.is_bought).length || 0,
        updatedAt: "עודכן כרגע" 
      }));

      setLists(formattedLists);
    } catch (e) {
      console.error("Failed to load lists:", e);
    } finally {
      setLoading(false);
    }
  }, [homeId]);

  // --- הגדרת Realtime ---
  useEffect(() => {
    if (!homeId) return;

    // טעינה ראשונית
    loadLists();

    // יצירת ערוץ האזנה לשינויים בטבלה
    const channel = supabase
      .channel(`realtime:shopping_lists:${homeId}`)
      .on(
        "postgres_changes",
        {
          event: "*", // INSERT, UPDATE, DELETE
          schema: "public",
          table: "shopping_lists",
          filter: `home_id=eq.${homeId}`,
        },
        () => {
          // כשמשהו משתנה ב-DB, נטען מחדש
          loadLists();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [homeId, loadLists]);

  // --- פונקציות עזר ---
  const handleCreate = async () => {
    if (!newListName.trim() || !homeId) return;
    try {
      setCreating(true);
      await createShoppingList({ home_id: homeId, name: newListName.trim() });
      setNewListName("");
      // בגלל ה-Realtime, הרשימה תתעדכן לבד, אבל נקרא לזה שוב ליתר ביטחון/מהירות
      loadLists();
    } catch (e) {
      Alert.alert("שגיאה", "לא הצלחנו ליצור את הרשימה");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteList = async (listId: string) => {
    try {
      // עדכון UI אופטימי (מחיקה מיידית מהמסך)
      setLists(prev => prev.filter(l => l.id !== listId));
      await deleteShoppingList(listId); 
    } catch (e) {
      Alert.alert("שגיאה", "לא הצלחנו למחוק את הרשימה");
      loadLists(); // טעינה מחדש במקרה של כישלון
    }
  };

  const handleBack = () => {
    if (homeId) {
      router.replace({
        pathname: "/home/[homeId]",
        params: { homeId },
      });
    } else {
      router.back();
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient 
          colors={[BRAND.PRIMARY_SOFT, BRAND.BG]} 
          style={StyleSheet.absoluteFill} 
        />
        
        <ScreenHeader title="רשימות קניות" onBack={handleBack} />

        {loading && lists.length === 0 ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={BRAND.PRIMARY} />
          </View>
        ) : (
          <FlatList
            data={lists}
            keyExtractor={(item) => item.id}
            contentContainerStyle={[
              styles.listContent, 
              { paddingBottom: 100 + insets.bottom }
            ]}
            ListHeaderComponent={
              <ShoppingListsHeader 
                newListName={newListName} 
                setNewListName={setNewListName}
                onCreate={handleCreate} 
                creating={creating} 
                listsCount={lists.length}
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
            ListEmptyComponent={
              !loading ? (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyText}>אין עדיין רשימות קניות...</Text>
                </View>
              ) : null
            }
          />
        )}

        {/* Bottom Navigation */}
        <View style={styles.bottomBarContainer}>
          <View style={{ paddingBottom: insets.bottom }}>
            <BottomNavBar activeTab="shopping-list" />
          </View>
        </View>
      </SafeAreaView>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  safeArea: { 
    flex: 1, 
    backgroundColor: BRAND.BG 
  },
  center: { 
    flex: 1, 
    justifyContent: "center", 
    alignItems: "center" 
  },
  listContent: { 
    padding: 16 
  },
  emptyState: { 
    alignItems: "center", 
    marginTop: 40 
  },
  emptyText: { 
    color: BRAND.MUTED, 
    fontSize: 16 
  },
  bottomBarContainer: { 
    position: "absolute", 
    bottom: 0, 
    left: 0, 
    right: 0, 
    backgroundColor: "rgba(255,255,255,0.96)", 
    borderTopWidth: 1, 
    borderTopColor: "#E5E7EB" 
  }
});