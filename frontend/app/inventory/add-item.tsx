import React, { useEffect, useMemo, useState, useCallback } from "react";
import { View, StyleSheet, Alert, ScrollView, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";

// UI Components
import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import ProductDraftCard from "@/src/components/add-item/ProductDraftCard";
import PendingList from "@/src/components/add-item/PendingList";
import LocationPickerModal from "@/src/components/add-item/LocationPickerModal";
import BarcodeScannerModal from "@/src/components/add-item/BarcodeScannerModal";
import DatePickerModal from "@/src/components/add-item/DatePickerModal";

// Logic & API
import { addProduct } from "@/src/api/stock";
import { searchCatalog, getCatalogByBarcode, type CatalogItem } from "@/src/api/catalog";
import { location_OPTIONS, routeTolocation, locationMap } from "@/src/components/add-item/types";
import { useDebouncedValue } from "@/src/hooks/useDebouncedValue";
import { setLastAddItemReturnDrafts } from "@/src/context/add-item-return-store";

// Custom Hooks & Utils
import { useBatchAddItems } from "@/src/hooks/useBatchAddItems";
import { normalizeCatalogList, normalizeCatalogOne } from "@/src/utils/batch-add-utils";
import { useMembershipGuard } from "@/src/hooks/useMembershipGuard"; // <--- ייבוא ה-Hook

const BRAND_BG = "#F4F4F4";

export default function BatchAddItemsScreen() {
  const insets = useSafeAreaInsets();
  const { homeId, location: locationParam, mode } = useLocalSearchParams<{
    homeId?: string;
    location?: string;
    mode?: string;
  }>();

  const isReceiptReviewMode = mode === "receipt-review";
  const currentHomeId = homeId ? String(homeId) : "";

  // הפעלת ההגנה: אם המשתמש הוסר מהבית בזמן שהוא מוסיף מוצרים, הוא ייזרק החוצה
  useMembershipGuard(currentHomeId);

  const initialLocation = useMemo(() => routeTolocation(locationParam), [locationParam]);

  const { draft, setters, pending, actions } = useBatchAddItems(initialLocation);

  const [suggestions, setSuggestions] = useState<CatalogItem[]>([]);
  const [nameLoading, setNameLoading] = useState(false);
  const [modals, setModals] = useState({ location: false, scan: false, date: false });

  const debouncedName = useDebouncedValue(draft.name.trim(), 250);
  const debouncedBarcode = useDebouncedValue(draft.barcode.trim(), 300);

  // --- search in catalog (הלוגיקה הקיימת שלך) ---
  
  useEffect(() => {
    if (draft.editingId || debouncedBarcode.length < 8) return;
    
    (async () => {
      try {
        const resp = await getCatalogByBarcode(debouncedBarcode);
        const item = normalizeCatalogOne(resp.data);
        if (item?.name) {
          setters.setSelectedCatalogItem(item);
          if (item.barcode) setters.setBarcode(item.barcode);
          setSuggestions([]);
          setters.setName("");
        }
      } catch (e) {}
    })();
  }, [debouncedBarcode, draft.editingId]);

  useEffect(() => {
    if (draft.editingId || draft.selectedCatalogItem || debouncedName.length < 2) {
      setSuggestions([]);
      return;
    }

    (async () => {
      setNameLoading(true);
      try {
        const resp = await searchCatalog(debouncedName);
        setSuggestions(normalizeCatalogList(resp.data).slice(0, 10));
      } catch {
        setSuggestions([]);
      } finally {
        setNameLoading(false);
      }
    })();
  }, [debouncedName, draft.editingId, draft.selectedCatalogItem]);

  // --- לוגיקת שמירה ---

  const onBulkAdd = async () => {
    if (isReceiptReviewMode) {
      handleReceiptReturn();
      return;
    }

    if (!currentHomeId) return Alert.alert("שגיאה", "חסר בית פעיל.");
    if (pending.length === 0) return Alert.alert("אין מוצרים", "הוסיפי מוצרים לרשימה.");

    try {
      const results = await Promise.allSettled(
        pending.map(item => addProduct(currentHomeId, {
          name: item.name,
          quantity: item.quantity,
          barcode: item.barcode || null,
          expiration_date: item.expiresAt?.toISOString().slice(0, 10),
          location: locationMap[item.location],
          nickname: item.nickname || null,
        }))
      );

      const failedIds = results
        .map((r, idx) => (r.status === "rejected" || (r as any).value?.status !== "success" ? pending[idx].id : null))
        .filter(id => id !== null) as string[];

      if (failedIds.length === 0) {
        Alert.alert("הצלחה!", "כל המוצרים נוספו למלאי.");
        router.back();
      } else {
        const successCount = pending.length - failedIds.length;
        actions.setPending(pending.filter(p => failedIds.includes(p.id)));
        Alert.alert("בוצע חלקית", `נוספו ${successCount} מוצרים. השארנו את השאר לניסיון חוזר.`);
      }
    } catch (e) {
      Alert.alert("שגיאה", "משהו השתבש בתהליך השמירה.");
    }
  };

  const canAdd = (draft.name.trim().length > 0 || draft.selectedCatalogItem !== null) && 
                (draft.quantity.length > 0 && parseInt(draft.quantity) > 0);

  const handleReceiptReturn = () => {
    const drafts = pending.map(p => ({
      name: p.name,
      quantity: p.quantity,
      barcode: p.barcode,
      nickname: p.nickname,
      expiration_date: p.expiresAt?.toISOString().slice(0, 10) || null,
      location: p.location,
    }));

    if (drafts.length === 0) {
        return Alert.alert("רשימה ריקה", "נא להוסיף לפחות מוצר אחד.");
    }

    setLastAddItemReturnDrafts(drafts);
    router.back();
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND_BG]} style={StyleSheet.absoluteFill} />

        <ScreenHeader 
          title={isReceiptReviewMode ? "הוספה לקבלה" : "הוספה מרובה"} 
          onBack={() => router.back()} 
        />

        <ScrollView
          contentContainerStyle={[styles.content, { paddingBottom: 140 + insets.bottom }]}
          keyboardShouldPersistTaps="handled"
        >
          <ProductDraftCard
            {...draft}
            editing={!!draft.editingId}
            locationOptions={location_OPTIONS}
            onChangeBarcode={setters.setBarcode}
            onChangeName={(v) => {
              setters.setName(v);
              if (draft.selectedCatalogItem) setters.setSelectedCatalogItem(null);
            }}
            onChangeNickname={setters.setNickname}
            onChangeQuantity={setters.setQuantity}
            onPresslocation={() => setModals(prev => ({ ...prev, location: true }))}
            onPressScan={() => setModals(prev => ({ ...prev, scan: true }))}
            onPressDate={() => setModals(prev => ({ ...prev, date: true }))}
            onClearDate={() => setters.setExpiresAt(undefined)}
            onAddToList={actions.upsertDraftToList}
            onCancelEdit={() => actions.resetDraft(true)}
            addDisabled={!canAdd}
            suggestions={suggestions}
            nameLoading={nameLoading}
            onPickSuggestion={(item) => {
              setters.setSelectedCatalogItem(item);
              if (item.barcode) setters.setBarcode(item.barcode);
              setSuggestions([]);
              setters.setName("");
            }}
            onClearSelectedCatalogItem={() => setters.setSelectedCatalogItem(null)}
          />

          <PendingList 
            items={pending} 
            locationOptions={location_OPTIONS} 
            onEdit={actions.loadItemToDraft} 
            onRemove={actions.removeFromList} 
          />
        </ScrollView>

        <View style={[styles.bottomBar, { paddingBottom: 16 + insets.bottom }]}>
          <PrimaryButton
            title={isReceiptReviewMode ? `סיום וחזרה לקבלה (${pending.length})` : `שמור במלאי (${pending.length})`}
            onPress={onBulkAdd}
            disabled={pending.length === 0}
            style={pending.length === 0 && { opacity: 0.6 }}
          />
        </View>

        {/* Modals */}
        <LocationPickerModal
          open={modals.location}
          selected={draft.location}
          options={location_OPTIONS}
          onClose={() => setModals(prev => ({ ...prev, location: false }))}
          onSelect={(c) => { setters.setLoc(c); setModals(prev => ({ ...prev, location: false })); }}
        />

        <BarcodeScannerModal 
          open={modals.scan} 
          onClose={() => setModals(prev => ({ ...prev, scan: false }))} 
          onScanned={(val) => setters.setBarcode(val)} 
        />

        <DatePickerModal
          open={modals.date}
          value={draft.expiresAt}
          onClose={() => setModals(prev => ({ ...prev, date: false }))}
          onChange={(d) => setters.setExpiresAt(d)}
          onClear={() => setters.setExpiresAt(undefined)}
        />
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: BRAND_BG },
  content: { padding: 16, gap: 12 },
  bottomBar: {
    position: "absolute",
    left: 0, right: 0, bottom: 0,
    padding: 16,
    backgroundColor: "rgba(244,244,244,0.95)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  }
});