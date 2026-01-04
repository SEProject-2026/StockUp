import type { Ionicons } from "@expo/vector-icons";

export type Category = "fridge" | "freezer" | "pantry" | "cleaning supplies" | "other";

export type DraftItem = {
  id: string;
  barcode: string | null;
  name: string;
  quantity: number;
  category: Category;
  expiresAt?: Date;
};

export const CATEGORY_OPTIONS: Array<{
  key: Category;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
}> = [
  { key: "fridge", label: "מקרר", icon: "snow-outline" },
  { key: "freezer", label: "מקפיא", icon: "cube-outline" },
  { key: "pantry", label: "מזווה", icon: "restaurant-outline" },
  { key: "cleaning supplies", label: "חומרי ניקוי", icon: "water-outline" },
  { key: "other", label: "אחר", icon: "ellipsis-horizontal-outline" },
];

export function routeToCategory(param?: string | null): Category {
  const raw = (param ?? "").trim();
  const normalized = raw.replace(/_/g, "-").replace(/\s+/g, "-").toLowerCase();
  switch (normalized) {
    case "fridge":
      return "fridge";
    case "freezer":
      return "freezer";
    case "pantry":
      return "pantry";
    case "cleaning-supplies":
    case "cleaningsupplies":
      return "cleaning supplies";
    case "other":
      return "other";
    default:
      return "fridge";
  }
}

export const locationMap: Record<Category, "FRIDGE" | "FREEZER" | "PANTRY" | "CLEANING_SUPPLIES" | "OTHER"> = {
  fridge: "FRIDGE",
  freezer: "FREEZER",
  pantry: "PANTRY",
  "cleaning supplies": "CLEANING_SUPPLIES",
  other: "OTHER",
};
