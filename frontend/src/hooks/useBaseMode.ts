import { useState, useEffect, useMemo } from "react";
import { Alert } from "react-native";

export type BaseLocation = "FRIDGE" | "FREEZER" | "PANTRY" | "CLEANING_SUPPLIES" | "OTHER";

export type BaseItem = {
  id: string;
  name: string;
  targetQty: number;
  unit?: string;
  location: BaseLocation;
};

export const LOCATIONS: BaseLocation[] = ["FRIDGE", "FREEZER", "PANTRY", "CLEANING_SUPPLIES", "OTHER"];

// --- API Placeholders (שמורים במלואם) ---
async function apiGetBaseMode(): Promise<BaseItem[]> {
  return [
    { id: "b1", name: "חלב 3%", targetQty: 2, unit: "יח׳", location: "FRIDGE" },
    { id: "b2", name: "ביצים", targetQty: 1, unit: "תבנית", location: "FRIDGE" },
    { id: "b3", name: "קוטג׳", targetQty: 3, unit: "יח׳", location: "FRIDGE" },
    { id: "b4", name: "עוף", targetQty: 1, unit: "יח׳", location: "FREEZER" },
    { id: "b5", name: "אפונה קפואה", targetQty: 2, unit: "יח׳", location: "FREEZER" },
    { id: "b6", name: "אורז", targetQty: 1, unit: "יח׳", location: "PANTRY" },
    { id: "b7", name: "פסטה", targetQty: 2, unit: "יח׳", location: "PANTRY" },
    { id: "b8", name: "נייר טואלט", targetQty: 2, unit: "חבילות", location: "CLEANING_SUPPLIES" },
    { id: "b9", name: "סבון כלים", targetQty: 1, unit: "יח׳", location: "CLEANING_SUPPLIES" },
  ];
}
async function apiCreateBaseItem(item: Omit<BaseItem, "id">): Promise<BaseItem> {
  return { id: `base_${Date.now()}`, ...item };
}
async function apiUpdateBaseItem(id: string, patch: Partial<BaseItem>): Promise<void> { return; }
async function apiDeleteBaseItem(id: string): Promise<void> { return; }

// --- Helpers ---
export function normalizeName(s: string) { return s.trim().toLowerCase(); }
export function locationLabel(loc: BaseLocation) {
  switch (loc) {
    case "FRIDGE": return "מקרר";
    case "FREEZER": return "מקפיא";
    case "PANTRY": return "מזווה";
    case "CLEANING_SUPPLIES": return "ניקיון";
    default: return "אחר";
  }
}
export function locationIcon(loc: BaseLocation) {
  switch (loc) {
    case "FRIDGE": return "snow-outline";
    case "FREEZER": return "snow";
    case "PANTRY": return "cube-outline";
    case "CLEANING_SUPPLIES": return "sparkles-outline";
    default: return "ellipsis-horizontal";
  }
}

export function useBaseMode() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<BaseItem[]>([]);
  const [query, setQuery] = useState("");
  const [busyIds, setBusyIds] = useState<string[]>([]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setItems(await apiGetBaseMode());
      } catch {
        Alert.alert("שגיאה", "לא הצלחתי לטעון מצב בסיס.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const totalTarget = useMemo(() => items.reduce((sum, x) => sum + (x.targetQty || 0), 0), [items]);

  const groupedSections = useMemo(() => {
    const q = normalizeName(query);
    return LOCATIONS.map((loc) => {
      const groupedItems = items
        .filter((item) => item.location === loc)
        .filter((item) => (q ? normalizeName(item.name).includes(q) : true))
        .sort((a, b) => a.name.localeCompare(b.name));
      return { location: loc, title: locationLabel(loc), items: groupedItems };
    }).filter((section) => section.items.length > 0);
  }, [items, query]);

  const markBusy = (id: string) => setBusyIds((prev) => (prev.includes(id) ? prev : [...prev, id]));
  const unmarkBusy = (id: string) => setBusyIds((prev) => prev.filter((x) => x !== id));

  const addItem = async (payload: Omit<BaseItem, "id">) => {
    const exists = items.some(x => normalizeName(x.name) === normalizeName(payload.name) && x.location === payload.location);
    if (exists) {
      Alert.alert("כבר קיים", "המוצר כבר קיים במצב בסיס באותו מיקום.");
      return;
    }
    try {
      const created = await apiCreateBaseItem(payload);
      setItems((prev) => [...prev, created]);
    } catch {
      Alert.alert("שגיאה", "לא הצלחתי להוסיף את הפריט.");
    }
  };

  const bumpQty = async (id: string, delta: number) => {
    const current = items.find((x) => x.id === id);
    if (!current) return;
    const nextQty = Math.max(1, current.targetQty + delta);
    if (nextQty === current.targetQty) return;
    const previousItems = items;
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, targetQty: nextQty } : it)));
    markBusy(id);
    try {
      await apiUpdateBaseItem(id, { targetQty: nextQty });
    } catch {
      setItems(previousItems);
      Alert.alert("שגיאה", "לא הצלחתי לעדכן את הכמות.");
    } finally {
      unmarkBusy(id);
    }
  };

  const removeItem = async (id: string) => {
    const previousItems = items;
    setItems((prev) => prev.filter((x) => x.id !== id));
    markBusy(id);
    try {
      await apiDeleteBaseItem(id);
    } catch {
      setItems(previousItems);
      Alert.alert("שגיאה", "לא הצלחתי למחוק את הפריט.");
    } finally {
      unmarkBusy(id);
    }
  };

  return {
    state: { loading, items, query, busyIds, totalTarget, groupedSections },
    actions: { setQuery, addItem, bumpQty, removeItem }
  };
}