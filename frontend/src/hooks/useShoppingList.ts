import { useState, useEffect, useMemo, useCallback } from "react";
import { Alert } from "react-native";
import { supabase } from "@/src/lib/supabase";
import { LOCATIONS, locationLabel } from "@/src/hooks/useBaseMode";

export type LocationKey = "FRIDGE" | "FREEZER" | "PANTRY" | "CLEANING" | "OTHER";

export type ShoppingItem = {
  id: string;
  name: string;
  quantity: number;
  location: LocationKey;
  is_bought: boolean;
};

export function useShoppingSections(filteredItems: ShoppingItem[]) {
  return useMemo(() => {
    const groups = new Map<string, ShoppingItem[]>();
    for (const item of filteredItems) {
      const loc = item?.location || "OTHER";
      if (!groups.has(loc)) groups.set(loc, []);
      groups.get(loc)!.push(item);
    }
    return LOCATIONS.filter((loc) => groups.has(loc)).map((loc) => ({
      location: loc as LocationKey,
      title: locationLabel(loc as any),
      items: groups.get(loc) || [],
    }));
  }, [filteredItems]);
}

export function useShoppingList({ homeId, listId }: { homeId: string; listId: string }) {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [mode, setMode] = useState<"EDIT" | "SHOPPING">("EDIT");
  const [query, setQuery] = useState("");
  const [modeSubmitting, setModeSubmitting] = useState(false);

  // סנכרון מול Supabase
  const syncToSupabase = async (newItems: ShoppingItem[]) => {
    try {
      const { error } = await supabase
        .from("shopping_lists")
        .update({ items: newItems })
        .eq("id", listId);
      if (error) throw error;
    } catch (e: any) {
      console.error("❌ [Sync] Error:", e.message);
      Alert.alert("שגיאה בסנכרון", "השינוי נשמר מקומית אך לא סונכרן לשרת");
    }
  };

  // טעינה ו-Realtime
  useEffect(() => {
    if (!listId) return;

    const fetchInitial = async () => {
      setLoading(true);
      try {
        const { data } = await supabase
          .from("shopping_lists")
          .select("items")
          .eq("id", listId)
          .single();
        
        if (data?.items && Array.isArray(data.items)) {
          const normalized = data.items.map((it: any) => ({
            id: it.id || it.item_name || Math.random().toString(36).substr(2, 9),
            name: it.name || it.item_name || "פריט ללא שם",
            quantity: it.quantity || 1,
            location: it.location || "OTHER",
            is_bought: it.is_bought ?? it.isBought ?? false
          }));
          setItems(normalized);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchInitial();

    const channel = supabase
      .channel(`list-sync-${listId}`)
      .on("postgres_changes", { event: "UPDATE", schema: "public", table: "shopping_lists", filter: `id=eq.${listId}` }, 
      (payload) => {
        if (payload.new?.items) {
          const normalized = payload.new.items.map((it: any) => ({
            id: it.id || it.item_name || Math.random().toString(),
            name: it.name || it.item_name || "פריט",
            quantity: it.quantity || 1,
            location: it.location || "OTHER",
            is_bought: it.is_bought ?? it.isBought ?? false
          }));
          setItems(normalized);
        }
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [listId]);

  useEffect(() => {
    const nextPicked: Record<string, boolean> = {};
    items.forEach(it => { nextPicked[it.id] = !!it.is_bought; });
    setPicked(nextPicked);
  }, [items]);

  // --- פעולות מתוקנות עם Functional Updates ---

  const addItem = useCallback(async (name: string, quantity: number = 1, source: string, location?: string) => {
    const cleanName = name.trim();
    if (!cleanName) return;

    const newItem: ShoppingItem = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 4),
      name: cleanName,
      quantity: Number(quantity) || 1,
      location: (location as LocationKey) || "OTHER",
      is_bought: false
    };

    setItems(prev => {
      if (prev.some(it => it.name.toLowerCase() === cleanName.toLowerCase())) {
        Alert.alert("כבר קיים", "המוצר כבר נמצא ברשימה.");
        return prev;
      }
      const updated = [...prev, newItem];
      syncToSupabase(updated);
      return updated;
    });
  }, [listId]);

  const removeItem = useCallback(async (id: string) => {
    setItems(prev => {
      const updated = prev.filter(it => it.id !== id);
      if (updated.length !== prev.length) syncToSupabase(updated);
      return updated;
    });
  }, [listId]);

  const togglePick = useCallback(async (id: string) => {
    setItems(prev => {
      const updated = prev.map(it => it.id === id ? { ...it, is_bought: !it.is_bought } : it);
      syncToSupabase(updated);
      return updated;
    });
  }, [listId]);

  const updateQuantity = useCallback(async (id: string, delta: number) => {
    setItems(prev => {
      const item = prev.find(it => it.id === id);
      if (!item) return prev;

      const newQty = (item.quantity || 1) + delta;
      if (newQty <= 0) {
        const updated = prev.filter(it => it.id !== id);
        syncToSupabase(updated);
        return updated;
      }

      const updated = prev.map(it => it.id === id ? { ...it, quantity: newQty } : it);
      syncToSupabase(updated);
      return updated;
    });
  }, [listId]);

const finishShopping = async (deletePicked: boolean) => {
  setModeSubmitting(true);
  
  setItems(prev => {
    let updated;
    
    if (deletePicked) {
      // אם המשתמש בחר לנקות את העגלה - מוחקים את מה שסומן
      updated = prev.filter(it => !it.is_bought);
    } else {
      // כאן התיקון: פשוט משאירים את המערך כפי שהוא! 
      // הפריטים שסומנו יישארו מסומנים (is_bought: true)
      updated = [...prev];
    }
    
    syncToSupabase(updated);
    return updated;
  });

  setMode("EDIT"); // חוזרים למצב עריכה
  setModeSubmitting(false);
};

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? items.filter((it) => it.name.toLowerCase().includes(q)) : items;
  }, [items, query]);

  return {
    mode, items, filteredItems, loading, picked, query, setQuery,
    modeSubmitting, addItem, removeItem, finishShopping, updateQuantity, togglePick,
    enterShoppingMode: () => setMode("SHOPPING")
  };
}