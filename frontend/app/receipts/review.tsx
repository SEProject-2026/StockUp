import React, { useMemo, useState, useEffect, useCallback } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { View, StyleSheet, Alert, FlatList, KeyboardAvoidingView, Platform, Text, Pressable } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";

import { getSelectedHomeId } from "../home/selected-home";
import { addProduct } from "@/src/api/stock";
import { consumeLastScannedReceipt } from "@/src/context/receipt-scan-store";
import { consumeLastAddItemReturnDrafts } from "@/src/context/add-item-return-store";

import ReviewHeader from "@/src/components/receipts/review/ReviewHeader";
import ReviewListItem from "@/src/components/receipts/review/ReviewListItem";
import ReviewFooter from "@/src/components/receipts/review/ReviewFooter";
import EditItemModal from "@/src/components/receipts/review/modals/EditItemModal";

import {
  BRAND,
  type DetectedItem,
  type LocationKey,
  parseReceiptParam,
  mapReceiptToDetectedItems,
  storagelocationToLocationType,
  uuid,
} from "@/src/components/receipts/review/review.shared";

function PrettyEmpty(props: { onAdd: () => void }) {
  return (
    <View style={styles.emptyWrap}>
      <View style={styles.emptyCard}>
        <View style={styles.emptyIconCircle}>
          <Ionicons name="receipt-outline" size={22} color={BRAND.TEXT} />
        </View>

        <Text style={styles.emptyTitle}>לא נמצאו מוצרים</Text>
        <Text style={styles.emptySub}>אפשר להוסיף מוצר ידנית דרך מסך ההוספה הרגיל.</Text>

        <Pressable onPress={props.onAdd} style={styles.emptyBtn}>
          <Ionicons name="add" size={18} color="#fff" />
          <Text style={styles.emptyBtnText}>הוספת מוצר</Text>
        </Pressable>
      </View>
    </View>
  );
}

export default function ReceiptReviewDetectedProductsScreen() {
  const { receipt } = useLocalSearchParams<{ receipt?: string }>();

  const receiptFromParam = useMemo(() => parseReceiptParam(receipt), [receipt]);
  const receiptObj = useMemo(() => receiptFromParam ?? consumeLastScannedReceipt(), [receiptFromParam]);

  const [items, setItems] = useState<DetectedItem[]>([]);
  const [editItem, setEditItem] = useState<DetectedItem | null>(null);
  const [saving, setSaving] = useState(false);

  const [query, setQuery] = useState("");
  const [activeLoc, setActiveLoc] = useState<LocationKey | "all">("all");

  useEffect(() => {
    setItems(mapReceiptToDetectedItems(receiptObj));
  }, [receiptObj]);

  useFocusEffect(
    useCallback(() => {
      const drafts = consumeLastAddItemReturnDrafts(); 
      if (!drafts.length) return;

      setItems((prev) => {
        const toAdd: DetectedItem[] = drafts.map((d) => ({
          id: uuid(),
          name: d.name,
          quantity: Number.isFinite(d.quantity) && d.quantity > 0 ? d.quantity : 1,
          location: d.location as any,
          storage_location: d.location as any,
          barcode: d.barcode ?? undefined,
        }));
        return [...toAdd, ...prev];
      });
    }, [])
  );

  const locationCounts = useMemo(() => {
    const c: Record<LocationKey, number> = { fridge: 0, freezer: 0, pantry: 0, cleaning: 0, other: 0 };
    for (const it of items) c[it.location ?? "other"]++;
    return c;
  }, [items]);

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((x) => {
      const okName = !q || x.name.toLowerCase().includes(q);
      const okLoc = activeLoc === "all" ? true : (x.location ?? "other") === activeLoc;
      return okName && okLoc;
    });
  }, [items, query, activeLoc]);

  const totalCount = items.length;
  const filteredCount = filteredItems.length;

  const onOpenAdd = useCallback(() => {
    router.push({ pathname: "/inventory/add-item", params: { mode: "receipt-review" } });
  }, []);

  const onConfirmAddAll = useCallback(async () => {
    if (saving) return;

    if (items.length === 0) {
      Alert.alert("אין מוצרים", "אין מה להוסיף למלאי.");
      return;
    }

    const payload = items.map((x) => ({
      name: x.name.trim(),
      quantity: Number.isFinite(x.quantity) ? x.quantity : 1,
      location: storagelocationToLocationType(x.location ?? x.storage_location ?? "other"),
    }));

    const bad = payload.find((p) => !p.name || p.quantity <= 0);
    if (bad) {
      Alert.alert("שגיאה", "ודאו שלכל מוצר יש שם וכמות תקינה.");
      return;
    }

    setSaving(true);
    let homeId: string | null = null;
    try {
      homeId = await getSelectedHomeId();
      if (!homeId) {
        Alert.alert("שגיאה", "לא נבחר בית פעיל. חזרו ובחרו בית.");
        return;
      }

      const results = await Promise.allSettled(payload.map((p) => addProduct(homeId!, p)));
      const ok = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.length - ok;

      if (failed === 0) {
        Alert.alert("התווסף!", "כל המוצרים הוכנסו למלאי המרכזי.", [
          {
            text: "אישור",
            onPress: () => {
              router.replace({ pathname: "/home/[homeId]", params: { homeId: homeId! } });
            },
          },
        ]);
        return;
      }

      Alert.alert("נוספו חלקית", `נוספו ${ok} מוצרים, נכשלו ${failed}.`);
    } catch (e: any) {
      Alert.alert("נכשל", e?.message ?? "לא הצלחנו להוסיף למלאי. נסו שוב.");
    } finally {
      setSaving(false);
      if (homeId) {
        router.replace({ pathname: "/home/[homeId]", params: { homeId } });
      }
    }
  }, [items, saving]);

  const renderItem = useCallback(
    ({ item }: { item: DetectedItem }) => <ReviewListItem item={item} onPress={() => setEditItem(item)} />,
    []
  );

  const keyExtractor = useCallback((it: DetectedItem) => it.id, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <LinearGradient colors={["#EEF6FF", BRAND.BG]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={StyleSheet.absoluteFill} />

        <ReviewHeader
          totalCount={totalCount}
          filteredCount={filteredCount}
          query={query}
          onChangeQuery={setQuery}
          locationCounts={locationCounts}
          onBack={() => router.back()}
          onOpenAdd={onOpenAdd}
          activeLocation={activeLoc}
          onChangeActiveLocation={setActiveLoc}
        />

        <FlatList
          data={filteredItems}
          keyExtractor={keyExtractor}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={<PrettyEmpty onAdd={onOpenAdd} />}
        />

        <ReviewFooter saving={saving} disabled={items.length === 0 || saving} onConfirm={onConfirmAddAll} />

        <EditItemModal
          item={editItem}
          onClose={() => setEditItem(null)}
          onSave={(updated) => {
            setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
            setEditItem(null);
          }}
          onDelete={(id) => {
            setItems((prev) => prev.filter((x) => x.id !== id));
            setEditItem(null);
          }}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: BRAND.BG },

  listContent: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 160,
    gap: 10,
  },

  emptyWrap: { padding: 18 },
  emptyCard: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 18,
    padding: 16,
    alignItems: "center",
    gap: 10,
  },
  emptyIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: BRAND.BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: BRAND.BLUE_LINE,
  },
  emptyTitle: { fontSize: 14, fontWeight: "900", color: BRAND.TEXT, textAlign: "center" },
  emptySub: { fontSize: 12, fontWeight: "700", color: BRAND.MUTED, textAlign: "center", lineHeight: 18 },

  emptyBtn: {
    marginTop: 8,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    backgroundColor: "#2563EB",
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 999,
  },
  emptyBtnText: { color: "#fff", fontWeight: "900" },
});
