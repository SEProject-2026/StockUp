// src/features/inventory/filters.constants.ts
import type { locationKey } from "@/src/components/inventory/inventory.utils";
import type { Ionicons } from "@expo/vector-icons";

export type StatusFilter = "all" | "soon" | "expired";

export const COLORS = {
  BRAND_BLUE_SOFT: "#F0F9FF",
  BRAND_TEXT: "#0F172A",
  BRAND_MUTED: "#64748B",
  ACCENT: "#0EA5E9",
  BORDER: "#E2E8F0",
  SUCCESS: "#10B981", // Emerald
  SUCCESS_SOFT: "#ECFDF5",
  WARNING: "#F59E0B", // Amber
  WARNING_SOFT: "#FFFBEB",
  DANGER: "#EF4444", // Red
  DANGER_SOFT: "#FEF2F2",
  CARD_BG: "#FFFFFF",
  BG_DIM: "#F8FAFC",
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
