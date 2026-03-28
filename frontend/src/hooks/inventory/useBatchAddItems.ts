import { useState, useCallback } from "react";
import { Alert } from "react-native";
import { location, DraftItem } from "@/src/components/add-item/types";
import { CatalogItem } from "@/src/api/catalog";
import { uid } from "../../utils/batch-add-utils";

export function useBatchAddItems(initialLocation: location) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [nickname, setNickname] = useState("");
  const [quantity, setQuantity] = useState("");
  const [loc, setLoc] = useState<location>(initialLocation);
  const [expiresAt, setExpiresAt] = useState<Date | undefined>(undefined);
  const [selectedCatalogItem, setSelectedCatalogItem] = useState<CatalogItem | null>(null);

  // List of products waiting to be saved
  const [pending, setPending] = useState<DraftItem[]>([]);

  const resetDraft = useCallback((keepLocation = true) => {
    setEditingId(null);
    setBarcode("");
    setName("");
    setNickname("");
    setQuantity("");
    if (!keepLocation) setLoc(initialLocation);
    setExpiresAt(undefined);
    setSelectedCatalogItem(null);
  }, [initialLocation]);

  const loadItemToDraft = useCallback((item: DraftItem) => {
    setEditingId(item.id);
    setBarcode(item.barcode ?? "");
    setName(item.name);
    setNickname(item.nickname ?? "");
    setQuantity(String(item.quantity));
    setLoc(item.location);
    setExpiresAt(item.expiresAt);
    setSelectedCatalogItem(null);
  }, []);

  const upsertDraftToList = useCallback(() => {
    const finalName = (selectedCatalogItem?.name || name.trim()).trim();
    const qty = parseInt(quantity, 10);

    if (!finalName || isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "נא להזין שם מוצר וכמות תקינה");
      return false;
    }

    const newItem: DraftItem = {
      id: editingId ?? uid(),
      barcode: barcode.trim() || null,
      name: finalName,
      nickname: nickname.trim() || null,
      quantity: qty,
      location: loc,
      expiresAt,
    };

    setPending((prev) => {
      const exists = prev.some((x) => x.id === newItem.id);
      if (!exists) return [newItem, ...prev];
      return prev.map((x) => (x.id === newItem.id ? newItem : x));
    });

    resetDraft(true);
    return true;
  }, [editingId, barcode, name, nickname, quantity, loc, expiresAt, selectedCatalogItem, resetDraft]);

  const removeFromList = useCallback((id: string) => {
    setPending((prev) => prev.filter((x) => x.id !== id));
    if (editingId === id) resetDraft(true);
  }, [editingId, resetDraft]);

  return {
    draft: { 
        editingId, barcode, name, nickname, quantity, 
        location: loc, expiresAt, selectedCatalogItem 
    },
    setters: { 
        setBarcode, setName, setNickname, setQuantity, 
        setLoc, setExpiresAt, setSelectedCatalogItem 
    },
    pending,
    actions: { resetDraft, loadItemToDraft, upsertDraftToList, removeFromList , setPending}
  };
}