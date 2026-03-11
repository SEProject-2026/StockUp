import React, { useMemo, useState, useEffect, useCallback } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  View,
  StyleSheet,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Text,
  Pressable,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";

import { getSelectedHomeId } from "@/src/utils/selected-home";
import { addReceipt } from "@/src/api/stock";
import { consumeLastScannedReceipt } from "@/src/context/receipt-scan-store";
import { consumeLastAddItemReturnDrafts } from "@/src/context/add-item-return-store";

import ReviewHeader from "@/src/components/receipts/review/ReviewHeader";
import ReviewListItem from "@/src/components/receipts/review/ReviewListItem";
import ReviewFooter from "@/src/components/receipts/review/ReviewFooter";
import EditItemModal from "@/src/components/receipts/review/modals/EditItemModal";
import { UnitType } from "@/src/components/receipts/review/review.shared";

import {
  BRAND,
  type DetectedItem,
  type LocationKey,
  needsAttention,
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

function toIsoDateOnly(s?: string | null) {
  if (!s) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  const d = new Date(s);
  if (Number.isNaN(+d)) return null;
  return d.toISOString().slice(0, 10);
}

export default function ReceiptReviewDetectedProductsScreen() {
  const { receipt } = useLocalSearchParams<{ receipt?: string }>();

  const receiptFromParam = useMemo(() => parseReceiptParam(receipt), [receipt]);
  const receiptObj = useMemo(
    () => receiptFromParam ?? consumeLastScannedReceipt(),
    [receiptFromParam]
  );

  const receiptChain = useMemo(() => {
  const inner = (receiptObj as any)?.data?.receipt ?? (receiptObj as any)?.data ?? receiptObj;
  const chain = inner?.chain ?? null;
  return chain ? String(chain) : null;
  }, [receiptObj]);


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
      if (!drafts || !drafts.length) return;

      setItems((prev) => {
        const toAdd: DetectedItem[] = drafts.map((d) => ({
          id: uuid(),
          name: d.name,
          nickname: d.nickname ?? undefined,
          quantity: Number.isFinite(d.quantity) && d.quantity > 0 ? d.quantity : 1,
          unit: d.unit ?? UnitType.UNIT, 
          weight: null,           
          location: (d.location as any) ?? "other",
          storage_location: (d.location as any) ?? "other",
          barcode: d.barcode ?? undefined,
          expiration_date: d.expiration_date ?? undefined,
        }));

        return [...toAdd, ...prev];
      });
    }, [])
  );

  const locationCounts = useMemo(() => {
    const c: Record<LocationKey, number> = {
      fridge: 0,
      freezer: 0,
      pantry: 0,
      cleaning: 0,
      other: 0,
    };
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

  const hasBlocking = useMemo(() => items.some(needsAttention), [items]);

  const onConfirmAddAll = useCallback(async () => {
    if (hasBlocking) {
      Alert.alert("חסרים פרטים", "יש שורות אדומות שדורשות השלמה/אישור לפני הוספה למלאי.");
      return;
    }

    if (saving) return;

    if (items.length === 0) {
      Alert.alert("אין מוצרים", "אין מה להוסיף למלאי.");
      return;
    }

    const receiptItems = items.map((x: any) => ({
      name: String(x.name ?? "").trim(),
      barcode: x.barcode ? String(x.barcode) : null,
      nickname: x.nickname ? String(x.nickname).trim() : null,
      expiration_date: toIsoDateOnly(x.expiration_date ?? null),
      location: storagelocationToLocationType(x.location ?? x.storage_location ?? "other"),
      quantity: x.quantity,
      unit: x.unit ?? "UNIT",
      weight: x.weight ?? null,
    }));


    const bad = receiptItems.find((p) => !p.name || p.quantity <= 0);
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
      const res = await addReceipt(homeId, {chain: receiptChain, items: receiptItems,});

      if (res.status === "success") {
        const added = res.data?.added_count ?? receiptItems.length;

        Alert.alert("התווסף!", `נוספו ${added} פריטים למלאי המרכזי.`, [
          {
            text: "אישור",
            onPress: () => {
              if (homeId) {
                router.replace({ pathname: "/home/[homeId]", params: { homeId } });
              }
            },
          },
        ]);
        return;
      }

      Alert.alert("נכשל", res.message ?? "לא הצלחנו להוסיף למלאי. נסו שוב.");
    } catch (e: any) {
      Alert.alert("נכשל", e?.message ?? "לא הצלחנו להוסיף למלאי. נסו שוב.");
    } finally {
      setSaving(false);
    }
  },[items, saving, hasBlocking]);

  const renderItem = useCallback(
    ({ item }: { item: DetectedItem }) => (
      <ReviewListItem item={item} onPress={() => setEditItem(item)} />
    ),
    []
  );

  const keyExtractor = useCallback((it: DetectedItem) => it.id, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <LinearGradient
          colors={["#EEF6FF", BRAND.BG]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={StyleSheet.absoluteFill}
        />

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

        <ReviewFooter
          saving={saving}
          disabled={items.length === 0 || saving || hasBlocking}
          onConfirm={onConfirmAddAll}
        />

        <EditItemModal
          item={editItem}
          onClose={() => setEditItem(null)}
          onSave={(updated: any) => {
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
