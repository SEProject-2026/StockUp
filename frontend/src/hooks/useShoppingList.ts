import { useState, useEffect, useMemo } from "react";
import { Alert } from "react-native";
import { LOCATIONS, locationLabel } from "@/src/hooks/useBaseMode";

export type LocationKey =
  | "FRIDGE"
  | "FREEZER"
  | "PANTRY"
  | "CLEANING"
  | "OTHER";

export type ShoppingItem = {
  id: string;
  name: string;
  quantity?: number;
  source?: "manual" | "suggestion" | "baseline_sync";
  location?: LocationKey;
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
export function useShoppingSections(filteredItems: any[]) {
  const groupedSections = useMemo(() => {
    const groups = new Map();

    for (const item of filteredItems) {
      const loc = item?.location || "UNSORTED";
      if (!groups.has(loc)) groups.set(loc, []);
      groups.get(loc).push(item);
    }

    const orderedKnown = LOCATIONS.filter((loc) => groups.has(loc)).map((loc) => ({
      location: loc,
      title: locationLabel(loc as any),
      items: groups.get(loc) || [],
    }));

    const unsorted = groups.has("UNSORTED")
      ? [{ location: "UNSORTED", title: "ללא מיקום", items: groups.get("UNSORTED") }]
      : [];

    return [...orderedKnown, ...unsorted];
  }, [filteredItems]);

  return groupedSections;
}
export function useShoppingList({ homeId, listId }: UseShoppingListParams) {
  const [mode, setMode] = useState<"EDIT" | "SHOPPING">("EDIT");
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function loadData() {
      if (!homeId || !listId) {
        setItems([]);
        setSuggestions([]);
        setPicked({});
        setLoading(false);
        return;
      }

      try {
        setLoading(true);

        const list: ShoppingItem[] = [
          {
            id: "1",
            name: "חלב 3%",
            quantity: 2,
            source: "manual",
            location: "FRIDGE",
          },
          {
            id: "2",
            name: "לחם",
            quantity: 1,
            source: "manual",
            location: "PANTRY",
          },
        ];

        const sugg: SuggestionItem[] = [
          { id: "s1", name: "ביצים", reason: "נרכש לעיתים קרובות" },
          { id: "s2", name: "גבינה צהובה", reason: "חסר לפי הרגלי צריכה" },
        ];

        setItems(list);
        setSuggestions(sugg);
        setPicked({});
      } catch (e) {
        Alert.alert("שגיאה", "לא הצלחתי לטעון את הרשימה");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [homeId, listId]);

  const existingNamesSet = useMemo(() => {
    return new Set(items.map((it) => it.name.trim().toLowerCase()));
  }, [items]);

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? items.filter((it) => it.name.toLowerCase().includes(q)) : items;
  }, [items, query]);

  const addItem = (
    name: string,
    quantity?: number,
    source: ShoppingItem["source"] = "manual",
    location?: LocationKey
  ) => {
    const cleanName = name.trim();

    if (!cleanName) return;

    if (existingNamesSet.has(cleanName.toLowerCase())) {
      Alert.alert("כבר קיים", "המוצר כבר נמצא ברשימה.");
      return;
    }

    const newItem: ShoppingItem = {
      id: `item_${Math.random().toString(16).slice(2)}`,
      name: cleanName,
      quantity: quantity ?? 1,
      source,
      location,
    };

    setItems((prev) => [newItem, ...prev]);
  };

  const removeItem = (id: string) => {
    setItems((prev) => prev.filter((x) => x.id !== id));
    setPicked((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  };

  const updateQuantity = (id: string, delta: number) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;

        const currentQty = item.quantity ?? 1;
        const newQty = Math.max(1, currentQty + delta);

        return { ...item, quantity: newQty };
      })
    );
  };

  const togglePick = (id: string) => {
    setPicked((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const finishShopping = async () => {
    const purchasedIds = Object.keys(picked).filter((id) => picked[id]);

    if (purchasedIds.length === 0) return;

    setItems((prev) => prev.filter((it) => !purchasedIds.includes(it.id)));
    setPicked({});
    setMode("EDIT");
  };

  return {
    mode,
    setMode,
    items,
    filteredItems,
    suggestions,
    loading,
    picked,
    togglePick,
    query,
    setQuery,
    addItem,
    removeItem,
    finishShopping,
    existingNamesSet,
    updateQuantity,
  };
}