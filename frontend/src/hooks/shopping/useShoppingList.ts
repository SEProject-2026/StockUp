import { useState, useEffect, useMemo, useCallback } from "react";
import { Alert } from "react-native";
import {
  getShoppingList,
  addItemToShoppingList,
  updateShoppingListItemQuantity,
  checkShoppingListItemAsBought,
  enterShoppingMode as enterShoppingModeApi,
  exitShoppingMode as exitShoppingModeApi,
  type ShoppingListDTO,
  type LocationType,
  deleteShoppingListItem,
} from "@/src/api/shoppingLists";

export type LocationKey = string;

export type ShoppingItem = {
  id: string;
  name: string;
  quantity?: number;
  source?: "manual" | "suggestion" | "baseline_sync";
  location?: LocationKey;
  isBought?: boolean;
};

export type SuggestionItem = {
  id: string;
  name: string;
  reason?: string;
};

type UseShoppingListParams = {
  homeId: string;
  listId: string;
};

function normalizeLocation(value?: string | null): LocationKey {
  return value || "OTHER";
}

function mapDtoToItems(dto: ShoppingListDTO): ShoppingItem[] {
  return dto.items.map((item) => ({
    id: item.item_name,
    name: item.item_name,
    quantity: item.quantity,
    source: "manual",
    location: normalizeLocation(item.location),
    isBought: item.is_bought,
  }));
}

export function useShoppingList({ homeId, listId }: UseShoppingListParams) {
  const [mode, setMode] = useState<"EDIT" | "SHOPPING">("EDIT");
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState("");
  const [modeSubmitting, setModeSubmitting] = useState(false);

  const syncFromDto = useCallback((dto: ShoppingListDTO) => {
    const mappedItems = mapDtoToItems(dto);
    setItems(mappedItems);
    setMode(dto.is_active_shopping_mode ? "SHOPPING" : "EDIT");

    const nextPicked: Record<string, boolean> = {};
    for (const item of mappedItems) {
      nextPicked[item.id] = !!item.isBought;
    }
    setPicked(nextPicked);
  }, []);

  const loadData = useCallback(async () => {
    if (!homeId || !listId) {
      setItems([]);
      setSuggestions([]);
      setPicked({});
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      const dto = await getShoppingList(listId);
      syncFromDto(dto);

      setSuggestions([]);
    } catch (e) {
      const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי לטעון את הרשימה";

      Alert.alert(
        "שגיאה",
        message
      );
    } finally {
      setLoading(false);
    }
  }, [homeId, listId, syncFromDto]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const existingNamesSet = useMemo(() => {
    return new Set(items.map((it) => it.name.trim().toLowerCase()));
  }, [items]);

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? items.filter((it) => it.name.toLowerCase().includes(q)) : items;
  }, [items, query]);

  const addItem = useCallback(
    async (
      name: string,
      quantity?: number,
      source: ShoppingItem["source"] = "manual",
      location?: LocationKey
    ) => {
      const cleanName = name.trim();

      if (!cleanName || !listId) return;

      if (existingNamesSet.has(cleanName.toLowerCase())) {
        Alert.alert("כבר קיים", "המוצר כבר נמצא ברשימה.");
        return;
      }

      try {
        const dto = await addItemToShoppingList(listId, {
          item_name: cleanName,
          quantity: quantity ?? 1,
          location: (location ?? "OTHER") as LocationType,
        });

        syncFromDto(dto);
      } catch (e) {
          const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי להוסיף את המוצר";
        Alert.alert(
          "שגיאה",
          message
        );
      }
    },
    [existingNamesSet, listId, syncFromDto]
  );

  const removeItem = useCallback(
    async (id: string) => {
      const current = items.find((x) => x.id === id);
      if (!current || !listId) return;

      try {
        const dto = await deleteShoppingListItem(listId, current.name);
        syncFromDto(dto);
      } catch (e) {
        console.error("Full Error Object:", e); // זה ידפיס ללוג של ה-VSCode/Terminal
        const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי למחוק את הפריט";
        Alert.alert("שגיאה", message);
        
      }
    },
    [items, listId, syncFromDto]
  );

  const updateQuantity = useCallback(
    async (id: string, delta: number) => {
      const current = items.find((item) => item.id === id);
      if (!current || !listId) return;

      const currentQty = current.quantity ?? 1;
      const newQty = currentQty + delta;

      if (newQty <= 0) {
        await removeItem(id);
        return;
      }

      try {
        const dto = await updateShoppingListItemQuantity(listId, current.name, newQty);
        syncFromDto(dto);
      } catch (e) {
        const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי לעדכן את הכמות";
        Alert.alert("שגיאה", message);
      }
    },
    [items, listId, syncFromDto, removeItem]
  );

  const togglePick = useCallback(
    async (id: string) => {
      const current = items.find((item) => item.id === id);
      if (!current || !listId) return;

      try {
        const dto = await checkShoppingListItemAsBought(listId, current.name);
        syncFromDto(dto);
      } catch (e) {
        const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי לעדכן את סימון המוצר";
        Alert.alert("שגיאה", message);
      }
    },
    [items, listId, syncFromDto]
  );

  const enterShoppingMode = useCallback(async () => {
    if (!listId) return;

    try {
      setModeSubmitting(true);
      const dto = await enterShoppingModeApi(listId);
      syncFromDto(dto);
      return dto;
    } catch (e) {
      const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי להפעיל את מצב הקנייה";
      Alert.alert("שגיאה", message);
    } finally {
      setModeSubmitting(false);
    }
  }, [listId, syncFromDto]);

  const finishShopping = useCallback(
    async (clear = true) => {
      if (!listId) return;

      try {
        setModeSubmitting(true);
        const dto = await exitShoppingModeApi(listId, { clear });
        syncFromDto(dto);
        return dto;
      } catch (e) {
        const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "לא הצלחתי לסיים את מצב הקנייה";
        Alert.alert(
          "שגיאה",
          message
        );
      } finally {
        setModeSubmitting(false);
      }
    },
    [listId, syncFromDto]
  );

  return {
    mode,
    setMode,
    items,
    filteredItems,
    loading,
    picked,
    togglePick,
    query,
    setQuery,
    addItem,
    removeItem,
    finishShopping,
    updateQuantity,
    enterShoppingMode,
    modeSubmitting,
  };
}