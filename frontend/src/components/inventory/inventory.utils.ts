import { location, InventoryItem } from "@/src/context/inventory-context";
import type { ProductDTO, LocationType, ExpirationType } from "@/src/api/stock";

export type InventoryRow = InventoryItem & {
  productId: string;
  itemId: string;

  expirationDate: string | null;
  originalName: string;
  hasNickname: boolean;

  status?: ExpirationType;
};

export type locationKey = location | "all";
export type StatusFilter = "all" | "soon" | "expired";

// ----- Group VM (what the list wants) -----
export type ProductGroupVM = {
  key: string; // unique: productId + originalName (extra safety)
  productId: string;

  title: string; // nickname if exists else original
  subtitle?: string; // original (only if nickname exists)

  // used for sorting/search
  originalName: string;
  nickname?: string | null;

  totalQuantity: number;

  sections: Array<{
    location: location; // ui
    totalQuantity: number;
    items: InventoryRow[];
  }>;
};

// Backend LocationType -> UI location
export function mapLocationTolocation(loc?: string | null): location {
  switch ((loc ?? "").toUpperCase()) {
    case "FRIDGE":
      return "fridge";
    case "FREEZER":
      return "freezer";
    case "PANTRY":
      return "pantry";
    case "CLEANING":
      return "cleaning";
    case "OTHER":
    default:
      return "other";
  }
}

// UI location -> Backend LocationType
export function locationToLocationType(cat: location): LocationType {
  switch (cat) {
    case "fridge":
      return "FRIDGE";
    case "freezer":
      return "FREEZER";
    case "pantry":
      return "PANTRY";
    case "cleaning":
      return "CLEANING";
    case "other":
    default:
      return "OTHER";
  }
}

export function statusFilterToExpirationType(sf: StatusFilter): ExpirationType | null {
  if (sf === "soon") return "GOING_TO_EXPIRE";
  if (sf === "expired") return "EXPIRED";
  return null;
}

export function toIsoDateOnly(s?: string | null) {
  if (!s) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;

  const d = new Date(s);
  if (Number.isNaN(+d)) return null;
  return d.toISOString().slice(0, 10);
}

export function dtoToRows(dto: ProductDTO): InventoryRow[] {
  const nick = dto.nickname?.trim() ? dto.nickname.trim() : "";
  const hasNickname = nick.length > 0;
  const displayName = hasNickname ? nick : dto.original_name;

  if (dto.items?.length) {
    return dto.items.map((it) => {
      const exp = it.expiration_date ? String(it.expiration_date) : null;

      return {
        id: String(it.id), // InventoryItem.id -> itemId
        name: displayName,
        quantity: it.quantity,
        location: mapLocationTolocation(it.location),
        expiresAt: exp ?? undefined,

        productId: String(dto.id),
        itemId: String(it.id),

        expirationDate: exp,
        originalName: dto.original_name,
        hasNickname,
        status: it.status,
      };
    });
  }

  // fallback
  return [
    {
      id: `${dto.id}__fallback`,
      name: displayName,
      quantity: dto.total_quantity ?? 0,
      location: "other",
      expiresAt: undefined,

      productId: String(dto.id),
      itemId: `${dto.id}__fallback`,

      expirationDate: null,
      originalName: dto.original_name,
      hasNickname,
      status: undefined,
    },
  ];
}

export function rowsSignature(rows: InventoryRow[]) {
  const sorted = [...rows].sort((a, b) => a.id.localeCompare(b.id));
  return sorted
    .map(
      (r) =>
        `${r.id}:${r.productId}:${r.itemId}:${r.quantity}:${r.expiresAt ?? ""}:${r.name}:${r.originalName}:${
          r.hasNickname ? 1 : 0
        }:${r.status ?? ""}:${r.location}`
    )
    .join("|");
}

export function locationLabel(loc: location) {
  return loc === "fridge"
    ? "מקרר"
    : loc === "freezer"
    ? "מקפיא"
    : loc === "pantry"
    ? "מזווה"
    : loc === "cleaning"
    ? "חומרי ניקוי"
    : "אחר";
}

export function locationColor(loc: location) {
  return loc === "fridge"
    ? "#0284C7"
    : loc === "freezer"
    ? "#6366F1"
    : loc === "pantry"
    ? "#F97316"
    : loc === "cleaning"
    ? "#10B981"
    : "#6B7280";
}
