import { supabase } from "@/src/lib/supabase";

// --- Types ---
export type LocationType =
  | "FRIDGE"
  | "FREEZER"
  | "PANTRY"
  | "CLEANING"
  | "BATHROOM"
  | "LAUNDRY"
  | "OTHER";

export type ShoppingListItemDTO = {
  id?: string; // הוספתי אופציונלי לתאימות
  item_name: string;
  name?: string; // לתאימות עם ה-Hook החדש
  quantity: number;
  is_bought: boolean;
  location: LocationType;
};

export type ShoppingListDTO = {
  id: string;
  home_id: string;
  name: string;
  is_active_shopping_mode: boolean;
  items: ShoppingListItemDTO[];
  updated_at: string;
};

// --- API Functions (Supabase) ---

/**
 * טעינת כל רשימות הקניות של הבית
 */
export async function getHomeShoppingLists(
  homeId: string
): Promise<ShoppingListDTO[]> {
  const { data, error } = await supabase
    .from("shopping_lists")
    .select("*")
    .eq("home_id", homeId)
    .order("created_at", { ascending: false });

  if (error) {
    console.error("❌ Error fetching home lists:", error.message);
    throw error;
  }

  return (data || []) as ShoppingListDTO[];
}

/**
 * טעינת רשימה ספציפית לפי ID
 */
export async function getShoppingList(
  listId: string
): Promise<ShoppingListDTO> {
  const { data, error } = await supabase
    .from("shopping_lists")
    .select("*")
    .eq("id", listId)
    .single();

  if (error) {
    console.error("❌ Error fetching list:", error.message);
    throw error;
  }

  return data as ShoppingListDTO;
}

/**
 * יצירת רשימה חדשה בבית
 */
export async function createShoppingList(payload: {
  home_id: string;
  name: string;
}): Promise<ShoppingListDTO> {
  const { data, error } = await supabase
    .from("shopping_lists")
    .insert([
      {
        home_id: payload.home_id,
        name: payload.name,
        items: [],
        is_active_shopping_mode: false,
      },
    ])
    .select()
    .single();

  if (error) {
    console.error("❌ Error creating list:", error.message);
    throw error;
  }

  return data as ShoppingListDTO;
}

/**
 * מחיקת רשימת קניות שלמה
 */
export async function deleteShoppingList(listId: string): Promise<void> {
  const { error } = await supabase
    .from("shopping_lists")
    .delete()
    .eq("id", listId);

  if (error) {
    console.error("❌ Error deleting list:", error.message);
    throw error;
  }
}