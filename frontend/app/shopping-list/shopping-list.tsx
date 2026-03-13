import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  TextInput,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams, useFocusEffect } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";
import {
  getHomeShoppingLists,
  createShoppingList,
  type ShoppingListDTO,
} from "@/src/api/shoppingLists";

const BRAND = {
  BG: "#F4F4F4",
  TEXT: "#111827",
  MUTED: "#6B7280",
  BORDER: "#E5E7EB",
  PRIMARY: "#0284C7",
  PRIMARY_SOFT: "#E5F3FF",
  CARD: "#FFFFFF",
  SUCCESS: "#10B981",
};

type ShoppingListSummary = {
  id: string;
  name: string;
  itemsCount: number;
  pickedCount: number;
  updatedAt: string;
};

function formatUpdatedAt(dateString: string): string {
  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return "עודכן לאחרונה";
  }

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return "עודכן עכשיו";
  if (diffHours < 24) return `עודכן לפני ${diffHours} שעות`;
  if (diffDays === 1) return "עודכן אתמול";
  if (diffDays < 7) return `עודכן לפני ${diffDays} ימים`;

  return `עודכן ב־${date.toLocaleDateString("he-IL")}`;
}

function mapDtoToSummary(dto: ShoppingListDTO): ShoppingListSummary {
  const itemsCount = dto.items.length;
  const pickedCount = dto.items.filter((item) => item.is_bought).length;

  return {
    id: dto.id,
    name: dto.name,
    itemsCount,
    pickedCount,
    updatedAt: formatUpdatedAt(dto.updated_at),
  };
}

export default function ShoppingListsScreen() {
  const insets = useSafeAreaInsets();
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newListName, setNewListName] = useState("");
  const [lists, setLists] = useState<ShoppingListSummary[]>([]);

  const loadLists = useCallback(async () => {
    if (!homeId) {
      setLists([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getHomeShoppingLists(homeId);
      setLists(data.map(mapDtoToSummary));
    } catch (e) {
      Alert.alert(
        "שגיאה",
        e instanceof Error ? e.message : "לא הצלחנו לטעון את רשימות הקניות."
      );
    } finally {
      setLoading(false);
    }
  }, [homeId]);

  useEffect(() => {
    loadLists();
  }, [loadLists]);

  useFocusEffect(
    useCallback(() => {
      loadLists();
    }, [loadLists])
  );

  const sortedLists = useMemo(() => {
    return [...lists].sort((a, b) => a.name.localeCompare(b.name, "he"));
  }, [lists]);

  const handleOpenList = (list: ShoppingListSummary) => {
    if (!homeId) {
      Alert.alert("שגיאה", "לא נמצא מזהה בית.");
      return;
    }

    router.push({
      pathname: "/shopping-list/[listId]",
      params: {
        homeId,
        listId: list.id,
        listName: list.name,
      },
    });
  };

  const handleCreateList = async () => {
    const trimmed = newListName.trim();

    if (!homeId) {
      Alert.alert("שגיאה", "לא נמצא מזהה בית.");
      return;
    }

    if (!trimmed) {
      Alert.alert("שם חסר", "צריך להזין שם לרשימה.");
      return;
    }

    try {
      setCreating(true);

      const created = await createShoppingList({
        home_id: homeId,
        name: trimmed,
      });

      const mapped = mapDtoToSummary(created);

      setLists((prev) => [mapped, ...prev]);
      setNewListName("");
    } catch (e) {
      Alert.alert(
        "שגיאה",
        e instanceof Error ? e.message : "לא הצלחנו ליצור רשימה חדשה."
      );
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ScreenHeader title="רשימות קניות" onBack={() => router.back()} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={BRAND.PRIMARY} />
          <Text style={styles.loadingText}>טוען רשימות קניות...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={[BRAND.PRIMARY_SOFT, BRAND.BG]}
        style={StyleSheet.absoluteFill}
      />

      <ScreenHeader title="רשימות קניות" onBack={() => router.back()} />

      <FlatList
        data={sortedLists}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{
          padding: 16,
          paddingBottom: 100 + insets.bottom,
        }}
        keyboardShouldPersistTaps="handled"
        ListHeaderComponent={
          <>
            <View style={styles.heroCard}>
              <View style={styles.heroIcon}>
                <Ionicons name="basket-outline" size={22} color={BRAND.PRIMARY} />
              </View>

              <View style={styles.heroTextWrap}>
                <Text style={styles.heroTitle}>כל רשימות הקניות של הבית</Text>
                <Text style={styles.heroSubtitle}>
                  אפשר ליצור כמה רשימות נפרדות ולנהל כל אחת בנפרד
                </Text>
              </View>
            </View>

            <View style={styles.createCard}>
              <Text style={styles.createTitle}>יצירת רשימה חדשה</Text>

              <View style={styles.inputRow}>
                <TextInput
                  value={newListName}
                  onChangeText={setNewListName}
                  placeholder="למשל: סופר, ניקיון, פארם..."
                  placeholderTextColor={BRAND.MUTED}
                  style={styles.input}
                  textAlign="right"
                />

                <TouchableOpacity
                  style={[styles.addButton, creating && styles.addButtonDisabled]}
                  activeOpacity={0.85}
                  onPress={handleCreateList}
                  disabled={creating}
                >
                  {creating ? (
                    <ActivityIndicator size="small" color="#FFF" />
                  ) : (
                    <Ionicons name="add" size={20} color="#FFF" />
                  )}
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>הרשימות שלך</Text>
              <Text style={styles.sectionMeta}>{lists.length} רשימות</Text>
            </View>
          </>
        }
        renderItem={({ item }) => {
          const progress =
            item.itemsCount > 0
              ? Math.round((item.pickedCount / item.itemsCount) * 100)
              : 0;

          return (
            <TouchableOpacity
              activeOpacity={0.9}
              style={styles.card}
              onPress={() => handleOpenList(item)}
            >
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
                  <Ionicons
                    name="checkmark-done-outline"
                    size={14}
                    color={BRAND.SUCCESS}
                  />
                  <Text style={styles.statText}>{item.pickedCount} סומנו</Text>
                </View>

                <View style={styles.statPill}>
                  <Ionicons name="pie-chart-outline" size={14} color={BRAND.TEXT} />
                  <Text style={styles.statText}>{progress}% הושלם</Text>
                </View>
              </View>
            </TouchableOpacity>
          );
        }}
        ListEmptyComponent={
          <View style={styles.emptyCard}>
            <Ionicons name="albums-outline" size={26} color={BRAND.MUTED} />
            <Text style={styles.emptyTitle}>עדיין אין רשימות קניות</Text>
            <Text style={styles.emptySubtitle}>
              צרי את הרשימה הראשונה של הבית כדי להתחיל
            </Text>
          </View>
        }
      />

      <View style={[styles.bottomBar, { paddingBottom: 10 + insets.bottom }]}>
        <BottomNavBar activeTab="shopping-list" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: BRAND.BG,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  loadingText: {
    marginTop: 8,
    color: BRAND.MUTED,
    fontWeight: "700",
  },
  heroCard: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 12,
    backgroundColor: "rgba(255,255,255,0.86)",
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E6EEF7",
    marginBottom: 14,
  },
  heroIcon: {
    width: 46,
    height: 46,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F0F9FF",
  },
  heroTextWrap: {
    flex: 1,
  },
  heroTitle: {
    textAlign: "right",
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 17,
  },
  heroSubtitle: {
    marginTop: 4,
    textAlign: "right",
    color: BRAND.MUTED,
    fontWeight: "600",
    fontSize: 13,
    lineHeight: 18,
  },
  createCard: {
    backgroundColor: BRAND.CARD,
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    marginBottom: 16,
  },
  createTitle: {
    textAlign: "right",
    color: BRAND.TEXT,
    fontSize: 15,
    fontWeight: "900",
    marginBottom: 10,
  },
  inputRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },
  input: {
    flex: 1,
    height: 46,
    borderRadius: 14,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    paddingHorizontal: 14,
    color: BRAND.TEXT,
    fontSize: 14,
    fontWeight: "700",
  },
  addButton: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: BRAND.PRIMARY,
    alignItems: "center",
    justifyContent: "center",
  },
  addButtonDisabled: {
    opacity: 0.7,
  },
  sectionHeader: {
    marginBottom: 10,
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
  },
  sectionTitle: {
    color: BRAND.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
  sectionMeta: {
    color: BRAND.MUTED,
    fontSize: 13,
    fontWeight: "700",
  },
  card: {
    backgroundColor: BRAND.CARD,
    borderRadius: 20,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },
  cardTopRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    marginBottom: 12,
  },
  arrowWrap: {
    marginLeft: 10,
  },
  cardTitleWrap: {
    flex: 1,
  },
  cardTitle: {
    textAlign: "right",
    color: BRAND.TEXT,
    fontSize: 16,
    fontWeight: "900",
  },
  cardSubtitle: {
    textAlign: "right",
    color: BRAND.MUTED,
    marginTop: 3,
    fontSize: 12,
    fontWeight: "600",
  },
  statsRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
  },
  statPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#F8FAFC",
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: "#E8EEF5",
  },
  statText: {
    color: BRAND.TEXT,
    fontSize: 12,
    fontWeight: "800",
  },
  emptyCard: {
    marginTop: 20,
    padding: 28,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.7)",
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: "#CBD5E1",
    alignItems: "center",
  },
  emptyTitle: {
    marginTop: 10,
    color: BRAND.TEXT,
    fontSize: 15,
    fontWeight: "900",
  },
  emptySubtitle: {
    marginTop: 6,
    color: BRAND.MUTED,
    fontSize: 13,
    fontWeight: "600",
    textAlign: "center",
    lineHeight: 18,
  },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255,255,255,0.94)",
    borderTopWidth: 1,
    borderTopColor: BRAND.BORDER,
  },
});