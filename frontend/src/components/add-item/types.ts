export type Category = "fridge" | "freezer" | "pantry" | "cleaning" | "other";

export type DraftItem = {
  id: string;
  name: string;
  nickname?: string | null;
  barcode?: string | null;
  quantity: number;
  category: Category;
  expiresAt?: Date;
};

export const locationMap: Record<Category, string> = {
  fridge: "FRIDGE",
  freezer: "FREEZER",
  pantry: "PANTRY",
  "cleaning": "CLEANING_SUPPLIES",
  other: "OTHER",
};

export const CATEGORY_OPTIONS: Array<{ key: Category; label: string; icon: any }> = [
  { key: "fridge", label: "מקרר", icon: "snow-outline" },
  { key: "freezer", label: "מקפיא", icon: "ice-cream-outline" },
  { key: "pantry", label: "מזווה", icon: "cube-outline" },
  { key: "cleaning", label: "חומרי ניקוי", icon: "sparkles-outline" },
  { key: "other", label: "אחר", icon: "ellipsis-horizontal-outline" },
];

export function routeToCategory(categoryParam?: string): Category {
  const c = String(categoryParam ?? "").toLowerCase();
  if (c === "fridge") return "fridge";
  if (c === "freezer") return "freezer";
  if (c === "pantry") return "pantry";
  if (c === "cleaning" || c === "cleaning_supplies") return "cleaning";
  if (c === "other") return "other";
  return "fridge";
}
