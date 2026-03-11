import { useState, useEffect, useMemo } from "react";
import { Alert } from "react-native";

export type ShoppingItem = {
  id: string;
  name: string;
  quantity?: number;
  source?: "manual" | "suggestion" | "baseline_sync";
};

export type SuggestionItem = {
  id: string;
  name: string;
  reason?: string;
};

export function useShoppingList() {
  const [mode, setMode] = useState<"EDIT" | "SHOPPING">("EDIT");
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [query, setQuery] = useState("");
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        // api
        const list = [
          { id: "1", name: "חלב 3%", quantity: 2, source: "manual" },
          { id: "2", name: "לחם", quantity: 1, source: "manual" },
        ] as ShoppingItem[];
        const sugg = [
          { id: "s1", name: "ביצים", reason: "נרכש לעיתים קרובות" },
          { id: "s2", name: "גבינה צהובה", reason: "חסר לפי הרגלי צריכה" },
        ] as SuggestionItem[];
        
        setItems(list);
        setSuggestions(sugg);
      } catch (e) {
        Alert.alert("שגיאה", "לא הצלחתי לטעון את הרשימה");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const existingNamesSet = useMemo(() => 
    new Set(items.map(it => it.name.trim().toLowerCase())), [items]
  );

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? items.filter(it => it.name.toLowerCase().includes(q)) : items;
  }, [items, query]);

  const addItem = (name: string, quantity?: number, source: ShoppingItem["source"] = "manual") => {
    const cleanName = name.trim();
    if (!cleanName) return;
    if (existingNamesSet.has(cleanName.toLowerCase())) {
      Alert.alert("כבר קיים", "המוצר כבר נמצא ברשימה.");
      return;
    }

    const newItem: ShoppingItem = {
      id: `item_${Math.random().toString(16).slice(2)}`,
      name: cleanName,
      quantity,
      source,
    };
    setItems(prev => [newItem, ...prev]);
  };

  const removeItem = (id: string) => {
    setItems(prev => prev.filter(x => x.id !== id));
    setPicked(prev => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  };
  const updateQuantity = (id: string, delta: number) => {
    setItems(prev => prev.map(item => {
      if (item.id === id) {
        const currentQty = item.quantity || 1;
        const newQty = Math.max(1, currentQty + delta); 
        return { ...item, quantity: newQty };
      }
      return item;
    }));
  };
  const togglePick = (id: string) => {
    setPicked(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const finishShopping = async () => {
    const purchasedIds = Object.keys(picked).filter(id => picked[id]);
    if (purchasedIds.length === 0) return;

    setItems(prev => prev.filter(it => !purchasedIds.includes(it.id)));
    setPicked({});
    setMode("EDIT");
  };

  return {
    mode, setMode,
    items, filteredItems,
    suggestions,
    loading,
    picked, togglePick,
    query, setQuery,
    addItem, removeItem,
    finishShopping,
    syncing, setSyncing,
    existingNamesSet,
    updateQuantity,
  };
}