import React, { useEffect, useMemo, useState } from "react";
import { View, StyleSheet, Alert, ScrollView, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";

import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import { addProduct, type LocationType } from "@/src/api/stock";

import { location_OPTIONS, routeTolocation, locationMap } from "@/src/components/add-item/types";
import type { location, DraftItem } from "@/src/components/add-item/types";

import ProductDraftCard from "@/src/components/add-item/ProductDraftCard";
import PendingList from "@/src/components/add-item/PendingList";
import LocationPickerModal from "@/src/components/add-item/LocationPickerModal";
import BarcodeScannerModal from "@/src/components/add-item/BarcodeScannerModal";
import DatePickerModal from "@/src/components/add-item/DatePickerModal";

import { useDebouncedValue } from "@/src/hooks/useDebouncedValue";
import { searchCatalog, getCatalogByBarcode, type CatalogItem } from "@/src/api/catalog";

import { setLastAddItemReturnDrafts, type AddItemReturnDraft } from "@/src/context/add-item-return-store";

const BRAND_BG = "#F4F4F4";

function uid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

function normalizeCatalogList(raw: any): CatalogItem[] {
  const arr =
    Array.isArray(raw)
      ? raw
      : Array.isArray(raw?.items)
      ? raw.items
      : Array.isArray(raw?.results)
      ? raw.results
      : [];

  return arr
    .map((x: any) => ({
      name: x.name ?? x.product_name ?? x.original_name ?? "",
      barcode: x.barcode ?? x.code ?? null,
      brand: x.brand ?? null,
      chain: x.chain ?? null,
    }))
    .filter((x: CatalogItem) => x.name);
}

function normalizeCatalogOne(raw: any): CatalogItem | null {
  if (!raw) return null;
  const name = raw.name ?? raw.product_name ?? raw.original_name ?? "";
  if (!name) return null;
  return {
    name,
    barcode: raw.barcode ?? raw.code ?? null,
    brand: raw.brand ?? null,
    chain: raw.chain ?? null,
  };
}

export default function BatchAddItemsScreen() {
  const { homeId, location: locationParam, mode } = useLocalSearchParams<{
    homeId?: string;
    location?: string;
    mode?: string;
  }>();

  const isReceiptReviewMode = mode === "receipt-review";
  const currentHomeId = homeId ? String(homeId) : "";

  const initiallocation = useMemo<location>(() => routeTolocation(locationParam), [locationParam]);

  const [editingId, setEditingId] = useState<string | null>(null);

  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [nickname, setNickname] = useState("");

  const [quantity, setQuantity] = useState("");
  const [location, setlocation] = useState<location>(initiallocation);
  const [expiresAt, setExpiresAt] = useState<Date | undefined>(undefined);

  const [selectedCatalogItem, setSelectedCatalogItem] = useState<CatalogItem | null>(null);

  const [suggestions, setSuggestions] = useState<CatalogItem[]>([]);
  const [nameLoading, setNameLoading] = useState(false);

  const [pending, setPending] = useState<DraftItem[]>([]);

  const [catOpen, setCatOpen] = useState(false);
  const [scanOpen, setScanOpen] = useState(false);
  const [dateOpen, setDateOpen] = useState(false);

  const selectedName = selectedCatalogItem?.name ?? name.trim();
  const canAddToList = selectedName.length > 0 && Number(quantity) > 0;

  const debouncedName = useDebouncedValue(name.trim(), 250);
  const debouncedBarcode = useDebouncedValue(barcode.trim(), 300);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (editingId) return;
      if (debouncedBarcode.length < 8) return;

      try {
        const resp = await getCatalogByBarcode(debouncedBarcode);
        if (cancelled) return;

        const item = normalizeCatalogOne(resp.data);
        if (item?.name) {
          setSelectedCatalogItem(item);
          if (item.barcode) setBarcode(item.barcode);
          setSuggestions([]);
          setName("");
        }
      } catch {}
    })();

    return () => {
      cancelled = true;
    };
  }, [debouncedBarcode, editingId]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (editingId) {
        setSuggestions([]);
        return;
      }

      if (selectedCatalogItem) {
        setSuggestions([]);
        return;
      }

      if (debouncedName.length < 2) {
        setSuggestions([]);
        return;
      }

      setNameLoading(true);
      try {
        const resp = await searchCatalog(debouncedName);
        if (cancelled) return;

        const items = normalizeCatalogList(resp.data);
        setSuggestions(items.slice(0, 10));
      } catch {
        if (!cancelled) setSuggestions([]);
      } finally {
        if (!cancelled) setNameLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [debouncedName, editingId, selectedCatalogItem]);

  function resetDraft(keeplocation = true) {
    setEditingId(null);
    setBarcode("");
    setName("");
    setNickname("");
    setQuantity("");
    if (!keeplocation) setlocation(initiallocation);
    setExpiresAt(undefined);

    setSelectedCatalogItem(null);
    setSuggestions([]);
    setNameLoading(false);
  }

  function loadItemToDraft(item: DraftItem) {
    setEditingId(item.id);
    setBarcode(item.barcode ?? "");
    setSelectedCatalogItem(null);
    setName(item.name);
    setNickname(item.nickname ?? "");
    setQuantity(String(item.quantity));
    setlocation(item.location);
    setExpiresAt(item.expiresAt);

    setSuggestions([]);
    setNameLoading(false);
  }

  function upsertDraftToList() {
    if (!canAddToList) return;

    const qty = parseInt(quantity, 10);
    if (Number.isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר חיובי");
      return;
    }

    const finalName = (selectedCatalogItem?.name ?? name.trim()).trim();

    const newItem: DraftItem = {
      id: editingId ?? uid(),
      barcode: barcode.trim() ? barcode.trim() : null,
      name: finalName,
      nickname: nickname.trim() ? nickname.trim() : null,
      quantity: qty,
      location,
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

  // ✅ receipt-review: מחזירים drafts למסך הקבלה – בלי שרת
function returnToReceiptReview() {
  const drafts: AddItemReturnDraft[] = [];

  for (const p of pending) {
    drafts.push({
      name: p.name.trim(),
      quantity: Number.isFinite(p.quantity) && p.quantity > 0 ? p.quantity : 1,
      barcode: p.barcode ?? null,
      nickname: p.nickname ?? null,
      expiration_date: p.expiresAt ? p.expiresAt.toISOString().slice(0, 10) : null,
      location: p.location, 
    });
  }

  if (drafts.length === 0) {
    const finalName = (selectedCatalogItem?.name ?? name.trim()).trim();
    const qty = parseInt(quantity, 10);

    if (finalName && Number.isFinite(qty) && qty > 0) {
      drafts.push({
        name: finalName,
        quantity: qty,
        barcode: barcode.trim() ? barcode.trim() : null,
        nickname: nickname.trim() ? nickname.trim() : null,
        expiration_date: expiresAt ? expiresAt.toISOString().slice(0, 10) : null,
        location: location, 
      });
    }
  }

  if (drafts.length === 0) {
    Alert.alert("אין מוצרים", "הוסיפי מוצר (או הוסיפי לרשימה) לפני חזרה למסך הקבלה.");
    return;
  }

  setLastAddItemReturnDrafts(drafts); // ✅ עכשיו אין שגיאה
  router.back();
}

  async function onBulkAdd() {
    // ✅ receipt-review mode: לא מוסיפים לשרת בכלל
    if (isReceiptReviewMode) {
      returnToReceiptReview();
      return;
    }

    // ✅ מצב רגיל: הוספה למלאי באמת
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
          location: locationMap[item.location], // ✅ enum
          nickname: item.nickname ?? null,
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

        <ScreenHeader title={isReceiptReviewMode ? "הוספת מוצר (לקבלה)" : "הוספה מרובה"} onBack={() => router.back()} />

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <ProductDraftCard
            editing={!!editingId}
            barcode={barcode}
            name={name}
            nickname={nickname}
            quantity={quantity}
            location={location}
            expiresAt={expiresAt}
            locationOptions={location_OPTIONS}
            onChangeBarcode={setBarcode}
            onChangeName={(v) => {
              setName(v);
              if (selectedCatalogItem) setSelectedCatalogItem(null);
              if (v.trim().length < 2) setSuggestions([]);
            }}
            onChangeNickname={setNickname}
            onChangeQuantity={setQuantity}
            onPresslocation={() => setCatOpen(true)}
            onPressScan={() => setScanOpen(true)}
            onPressDate={() => setDateOpen(true)}
            onClearDate={() => setExpiresAt(undefined)}
            onAddToList={upsertDraftToList}
            onCancelEdit={() => resetDraft(true)}
            addDisabled={!canAddToList}
            suggestions={suggestions}
            nameLoading={nameLoading}
            selectedCatalogItem={selectedCatalogItem}
            onClearSelectedCatalogItem={() => setSelectedCatalogItem(null)}
            onPickSuggestion={(item) => {
              setSelectedCatalogItem(item);
              if (item.barcode) setBarcode(item.barcode);
              setSuggestions([]);
              setName("");
            }}
          />

          <PendingList items={pending} locationOptions={location_OPTIONS} onEdit={loadItemToDraft} onRemove={removeFromList} />

          <View style={{ height: 90 }} />
        </ScrollView>

        <View style={styles.bottomBar}>
          <PrimaryButton
            title={
              isReceiptReviewMode
                ? `הוספה לרשימת הקבלה (${pending.length || (canAddToList ? 1 : 0)})`
                : `הוספה למלאי (${pending.length})`
            }
            onPress={onBulkAdd}
            disabled={isReceiptReviewMode ? pending.length === 0 && !canAddToList : pending.length === 0}
            style={[
              styles.saveButton,
              (isReceiptReviewMode ? pending.length === 0 && !canAddToList : pending.length === 0) && { opacity: 0.55 },
            ]}
          />
        </View>

        <LocationPickerModal
          open={catOpen}
          selected={location}
          options={location_OPTIONS}
          onClose={() => setCatOpen(false)}
          onSelect={(c) => {
            setlocation(c);
            setCatOpen(false);
          }}
        />

        <BarcodeScannerModal open={scanOpen} onClose={() => setScanOpen(false)} onScanned={(value) => setBarcode(value)} />

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
