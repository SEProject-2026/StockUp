import React, { ComponentProps, JSX } from "react";
import { View, Text } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";

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


export type LocationKey = "fridge" | "freezer" | "pantry" | "cleaning" | "other";
export type Storagelocation = LocationKey;

export type DetectedItem = {
  id: string;
  barcode?: string;
  name: string;
  quantity: number;
  unit?: string;

  storage_location?: Storagelocation;
  location: LocationKey;
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

export function storagelocationToLocationType(cat?: string | null): string {
  const s = String(cat ?? "").toLowerCase().trim();
  switch (s) {
    case "fridge":
      return "FRIDGE";
    case "freezer":
      return "FREEZER";
    case "pantry":
      return "PANTRY";
    case "cleaning":
      return "CLEANING_SUPPLIES";
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

export function mapReceiptToDetectedItems(receipt: any | null): DetectedItem[] {
  if (!receipt) return [];

  const inner = receipt?.data?.receipt ?? receipt?.data ?? receipt;
  const rawItems = inner.items ?? inner.detected_items ?? inner?.data?.items ?? [];
  if (!Array.isArray(rawItems)) return [];

  return rawItems
    .map((it: any) => {
      const name = String(it.name ?? it.product_name ?? it.title ?? "").trim();
      const qRaw = it.quantity ?? it.qty ?? 1;
      const quantity = Number(String(qRaw).replace(",", "."));
      const unit = it.unit ? String(it.unit) : undefined;

      if (!name) return null;

      const storage_location = it.storage_location ?? it.storagelocation ?? it.location;
      const normalizedCat = normalizelocation(storage_location);
      const location = locationToDefaultLocation(normalizedCat);

      return {
        id: uuid(),
        barcode: it.barcode ? String(it.barcode) : undefined,
        name,
        quantity: Number.isFinite(quantity) && quantity > 0 ? quantity : 1,
        unit,
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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
