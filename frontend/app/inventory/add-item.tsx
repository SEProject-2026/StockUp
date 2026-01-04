import React, { useMemo, useState } from "react";
import { View, StyleSheet, Alert, ScrollView, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";

import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/ui/PrimaryButton";
import { addProduct } from "@/src/api/stock";

import { CATEGORY_OPTIONS, routeToCategory, locationMap } from "@/src/components/add-item/types";
import type { Category, DraftItem } from "@/src/components/add-item/types";

import ProductDraftCard from "@/src/components/add-item/ProductDraftCard";
import PendingList from "@/src/components/add-item/PendingList";
import CategoryPickerModal from "@/src/components/add-item/CategoryPickerModal";
import BarcodeScannerModal from "@/src/components/add-item/BarcodeScannerModal";
import DatePickerModal from "@/src/components/add-item/DatePickerModal";

const BRAND_BG = "#F4F4F4";

function uid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

export default function BatchAddItemsScreen() {
  const { homeId, category: categoryParam } = useLocalSearchParams<{ homeId?: string; category?: string }>();
  const currentHomeId = homeId ? String(homeId) : "";

  const initialCategory = useMemo<Category>(() => routeToCategory(categoryParam), [categoryParam]);

  // Draft (שדות הטופס)
  const [editingId, setEditingId] = useState<string | null>(null);
  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [category, setCategory] = useState<Category>(initialCategory);
  const [expiresAt, setExpiresAt] = useState<Date | undefined>(undefined);

  // Pending list
  const [pending, setPending] = useState<DraftItem[]>([]);

  // Modals
  const [catOpen, setCatOpen] = useState(false);
  const [scanOpen, setScanOpen] = useState(false);
  const [dateOpen, setDateOpen] = useState(false);

  const canAddToList = name.trim().length > 0 && Number(quantity) > 0;

  function resetDraft(keepCategory = true) {
    setEditingId(null);
    setBarcode("");
    setName("");
    setQuantity("");
    if (!keepCategory) setCategory(initialCategory);
    setExpiresAt(undefined);
  }

  function loadItemToDraft(item: DraftItem) {
    setEditingId(item.id);
    setBarcode(item.barcode ?? "");
    setName(item.name);
    setQuantity(String(item.quantity));
    setCategory(item.category);
    setExpiresAt(item.expiresAt);
  }

  function upsertDraftToList() {
    if (!canAddToList) return;

    const qty = parseInt(quantity, 10);
    if (Number.isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר חיובי");
      return;
    }

    const newItem: DraftItem = {
      id: editingId ?? uid(),
      barcode: barcode.trim() ? barcode.trim() : null,
      name: name.trim(),
      quantity: qty,
      category,
      expiresAt,
    };

    setPending((prev) => {
      const exists = prev.some((x) => x.id === newItem.id);
      if (!exists) return [newItem, ...prev];
      return prev.map((x) => (x.id === newItem.id ? newItem : x));
    });

    resetDraft(true);
  }

  function removeFromList(id: string) {
    setPending((prev) => prev.filter((x) => x.id !== id));
    if (editingId === id) resetDraft(true);
  }

  async function onBulkAdd() {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "חסר בית פעיל. חזרי למסך הבתים ובחרי בית מחדש.");
      return;
    }
    if (pending.length === 0) {
      Alert.alert("אין מוצרים", "הוסיפי לפחות מוצר אחד לרשימה לפני שמירה.");
      return;
    }

    const results = await Promise.allSettled(
      pending.map(async (item) => {
        const formattedExpires = item.expiresAt ? item.expiresAt.toISOString().slice(0, 10) : undefined;

        const res = await addProduct(currentHomeId, {
          name: item.name,
          quantity: item.quantity,
          barcode: item.barcode ? item.barcode : null,
          expiration_date: formattedExpires,
          location: locationMap[item.category],
          nickname: null,
        });

        if (res.status !== "success") throw new Error(res.message ?? "הוספה נכשלה");
        return true;
      })
    );

    const successCount = results.filter((r) => r.status === "fulfilled").length;
    const failCount = results.length - successCount;

    if (failCount === 0) {
      Alert.alert("הצלחה!", `נוספו ${successCount} מוצרים למלאי.`);
      router.back();
      return;
    }

    const failedIds: string[] = [];
    results.forEach((r, idx) => {
      if (r.status === "rejected") failedIds.push(pending[idx].id);
    });
    setPending((prev) => prev.filter((x) => failedIds.includes(x.id)));

    Alert.alert("בוצע חלקית", `נוספו ${successCount} מוצרים.\nנכשלו ${failCount} — השארתי אותם ברשימה לנסות שוב.`);
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient
          colors={["#E5F3FF", BRAND_BG]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />

        <ScreenHeader title="הוספה מרובה" onBack={() => router.back()} />

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <ProductDraftCard
            editing={!!editingId}
            barcode={barcode}
            name={name}
            quantity={quantity}
            category={category}
            expiresAt={expiresAt}
            categoryOptions={CATEGORY_OPTIONS}
            onChangeBarcode={setBarcode}
            onChangeName={setName}
            onChangeQuantity={setQuantity}
            onPressCategory={() => setCatOpen(true)}
            onPressScan={() => setScanOpen(true)}
            onPressDate={() => setDateOpen(true)}
            onClearDate={() => setExpiresAt(undefined)}
            onAddToList={upsertDraftToList}
            onCancelEdit={() => resetDraft(true)}
            addDisabled={!canAddToList}
          />

          <PendingList
            items={pending}
            categoryOptions={CATEGORY_OPTIONS}
            onEdit={loadItemToDraft}
            onRemove={removeFromList}
          />

          <View style={{ height: 90 }} />
        </ScrollView>

        <View style={styles.bottomBar}>
          <PrimaryButton
            title={`הוספה למלאי (${pending.length})`}
            onPress={onBulkAdd}
            disabled={pending.length === 0}
            style={[styles.saveButton, pending.length === 0 && { opacity: 0.55 }]}
          />
        </View>

        <CategoryPickerModal
          open={catOpen}
          selected={category}
          options={CATEGORY_OPTIONS}
          onClose={() => setCatOpen(false)}
          onSelect={(c) => {
            setCategory(c);
            setCatOpen(false);
          }}
        />

        <BarcodeScannerModal
          open={scanOpen}
          onClose={() => setScanOpen(false)}
          onScanned={(value) => setBarcode(value)}
        />

        <DatePickerModal
          open={dateOpen}
          value={expiresAt}
          onClose={() => setDateOpen(false)}
          onChange={(d) => setExpiresAt(d)}
          onClear={() => setExpiresAt(undefined)}
        />
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: BRAND_BG },
  content: { padding: 16, paddingBottom: 140, gap: 12 },

  bottomBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 16,
    backgroundColor: "rgba(244,244,244,0.92)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  saveButton: {
    backgroundColor: "#0284C7",
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
});
