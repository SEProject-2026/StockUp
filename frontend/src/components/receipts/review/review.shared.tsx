import React, { ComponentProps, JSX } from "react";
import { View, Text } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import type { LocationType } from "@/src/api/stock";

export const BRAND = {
  BG: "#F5F6F8",
  CARD: "#FFFFFF",
  BORDER: "#E6E8EE",
  TEXT: "#111827",
  MUTED: "#6B7280",

  PRIMARY: "#0284C7",
  PRIMARY_SOFT: "#EAF2FF",
  PRIMARY_LINE: "#CFE2FF",

  BLUE_SOFT: "#F0FAFF",
  BLUE_LINE: "#DCEBFA",
} as const;

export enum UnitType {
  UNIT = "UNIT",
  KG = "KG",
}

export type LocationKey = "fridge" | "freezer" | "pantry" | "cleaning" | "other";
export type Storagelocation = LocationKey;

export type DetectedItem = {
  id: string;
  name: string;
  barcode?: string | null;
  nickname?: string | null;
  expiration_date?: string | null;
  location?: LocationKey;
  storage_location?: LocationKey;
  chain?: string | null;
  quantity: number;         // final quantity (units) to be stored
  unit: UnitType;           // UNIT | KG
  weight?: number | null;   // for weighted items only (kg float)

  // ✅ UI only
  units_count?: number | null;
  suggested_units?: number | null;
};

type IconProps = Omit<ComponentProps<typeof MaterialCommunityIcons>, "name">;

export const LOCATION_LABEL: Record<LocationKey, string> = {
  fridge: "מקרר",
  freezer: "מקפיא",
  pantry: "מזווה",
  cleaning: "ניקיון וטואלטיקה",
  other: "אחר",
};

export const LOCATION_ICON: Record<LocationKey, (props: IconProps) => JSX.Element> = {
  fridge: (props) => <MaterialCommunityIcons name="fridge-outline" {...props} />,
  freezer: (props) => <MaterialCommunityIcons name="snowflake-variant" {...props} />,
  pantry: (props) => <MaterialCommunityIcons name="food-variant" {...props} />,
  cleaning: (props) => <MaterialCommunityIcons name="spray-bottle" {...props} />,
  other: (props) => <MaterialCommunityIcons name="dots-horizontal" {...props} />,
};

export function uuid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

export function storagelocationToLocationType(cat?: string | null): LocationType {
  const s = String(cat ?? "").toLowerCase().trim();
  switch (s) {
    case "fridge":
      return "FRIDGE";
    case "freezer":
      return "FREEZER";
    case "pantry":
      return "PANTRY";
    case "cleaning":
      return "CLEANING";
    default:
      return "OTHER";
  }
}

export function normalizelocation(v: any): Storagelocation {
  const s = String(v ?? "").trim().toLowerCase();
  if (s === "fridge" || s === "freezer" || s === "pantry" || s === "cleaning" || s === "other") return s;
  return "other";
}

export function locationToDefaultLocation(cat?: any): LocationKey {
  return normalizelocation(cat);
}

export function parseReceiptParam(receiptParam?: string): any | null {
  if (!receiptParam) return null;
  try {
    return JSON.parse(receiptParam);
  } catch {}
  try {
    return JSON.parse(decodeURIComponent(receiptParam));
  } catch {}
  try {
    return JSON.parse(decodeURIComponent(decodeURIComponent(receiptParam)));
  } catch {}
  return null;
}

export function normalizeUnitType(v: any): UnitType {
  const s = String(v ?? "").trim().toUpperCase();
  if (s === "KG" || s === "ק\"ג" || s === "ק״ג" || s === "קג") return UnitType.KG;
  return UnitType.UNIT;
}

export function mapReceiptToDetectedItems(receipt: any | null): DetectedItem[] {
  
  if (!receipt) return [];

  const inner = receipt?.data?.receipt ?? receipt?.data ?? receipt;
  const rawItems = inner.items ?? inner.detected_items ?? inner?.data?.items ?? [];
  if (!Array.isArray(rawItems)) return [];

  return rawItems
    .map((it: any) => {
      const name = String(it.name ?? it.product_name ?? it.title ?? "").trim();
      if (!name) return null;

      // raw quantity
      const qRaw = it.quantity ?? it.qty ?? 1;
      const quantityNum = Number(String(qRaw).replace(",", "."));

      //  backend field: weight (kg float) if exists
      const weightNum =
        it.weight === null || it.weight === undefined
          ? null
          : Number(String(it.weight).replace(",", "."));
      const weight = weightNum !== null && Number.isFinite(weightNum) && weightNum > 0 ? weightNum : null;
      const unit = normalizeUnitType(it.unit);

      // location
      const storage_location = it.storage_location ?? it.storagelocation ?? it.location;
      const normalizedCat = normalizelocation(storage_location);
      const location = locationToDefaultLocation(normalizedCat);

      const initialQuantity =
        Number.isFinite(quantityNum) && quantityNum > 0 ? Math.round(quantityNum) : 1;

      return {
        id: uuid(),
        barcode: it.barcode ? String(it.barcode) : null,
        name,
        nickname: it.nickname ? String(it.nickname) : null,
        expiration_date: it.expiration_date ? String(it.expiration_date) : null,

        quantity: initialQuantity,
        unit: unit ?? UnitType.UNIT,
        weight,

        // UI-only if server provides them
        suggested_units:
          it.suggested_units && Number.isFinite(+it.suggested_units) ? Number(it.suggested_units) : null,
        units_count:
          it.units_count && Number.isFinite(+it.units_count) ? Number(it.units_count) : null,

        storage_location: normalizedCat,
        location,
        
      } as DetectedItem;
    })
    .filter(Boolean) as DetectedItem[];
}

export function PrimaryButtonCompat(props: {
  title: string;
  onPress: () => void;
  leftIcon?: React.ReactNode;
  disabled?: boolean;
}) {
  const { title, onPress, leftIcon, disabled } = props;
  const Btn: any = PrimaryButton;

  return (
    <Btn title={title} onPress={onPress} disabled={disabled}>
      <View style={{ flexDirection: "row-reverse", alignItems: "center", gap: 10 }}>
        {leftIcon}
        <Text style={{ fontWeight: "900", color: BRAND.TEXT, letterSpacing: 0.2 }}>{title}</Text>
      </View>
    </Btn>
  );
}

export function hasWeight(item: DetectedItem) {
  return typeof item.weight === "number" && item.weight > 0;
}

export function formatWeightKg(weight?: number | null) {
  if (!weight || !Number.isFinite(weight)) return "";
  return weight % 1 === 0 ? `${weight}` : `${weight.toFixed(2)}`.replace(/\.?0+$/, "");
}

export function needsAttention(item: DetectedItem) {
  if (!String(item.name ?? "").trim()) return true;
  if (!Number.isFinite(item.quantity) || item.quantity <= 0) return true;

  if (hasWeight(item)) {
    if (!item.units_count || item.units_count <= 0) return true;
  }
  return false;
}
