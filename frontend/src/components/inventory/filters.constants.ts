// src/features/inventory/filters.constants.ts
import type { locationKey } from "@/src/components/inventory/inventory.utils";
import type { Ionicons } from "@expo/vector-icons";

export type StatusFilter = "all" | "soon" | "expired";

export const COLORS = {
  BRAND_BLUE_SOFT: "#F0FAFF",
  BRAND_TEXT: "#111827",
  BRAND_MUTED: "#6B7280",
  ACCENT: "#0284C7",
  BORDER: "#E5E7EB",
} as const;

export const CATEGORIES: Array<{
  key: locationKey;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
}> = [
  { key: "all", label: "הכול", icon: "apps-outline" },
  { key: "fridge", label: "מקרר", icon: "snow-outline" },
  { key: "freezer", label: "מקפיא", icon: "cube-outline" },
  { key: "pantry", label: "מזווה", icon: "restaurant-outline" },
  { key: "cleaning", label: "חומרי ניקוי", icon: "water-outline" },
  { key: "other", label: "אחר", icon: "ellipsis-horizontal-outline" },
];

export const QUICK_KEYS: locationKey[] = ["all", "fridge", "freezer", "pantry"];
