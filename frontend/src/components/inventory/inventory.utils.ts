import { location, InventoryItem } from "@/src/context/inventory-context";
import type { ProductDTO, LocationType, ExpirationType } from "@/src/api/stock";

export type InventoryRow = InventoryItem & {
  productId: string;
  expirationDate: string | null;
  originalName: string;
  hasNickname: boolean;
  status?: string;
};

export type locationKey = location | "all";
export type StatusFilter = "all" | "soon" | "expired";

export function mapLocationTolocation(location?: string | null): location {
  switch ((location ?? "").toUpperCase()) {
    case "FRIDGE":
      return "fridge";
    case "FREEZER":
      return "freezer";
    case "PANTRY":
      return "pantry";
    case "CLEANING_SUPPLIES":
      return "cleaning";
    case "OTHER":
      return "other";
    default:
      return "other";
  }
}

export function locationToLocationType(cat: location): LocationType {
  switch (cat) {
    case "fridge":
      return "FRIDGE";
    case "freezer":
      return "FREEZER";
    case "pantry":
      return "PANTRY";
    case "cleaning":
      return "CLEANING_SUPPLIES";
    case "other":
      return "OTHER";
    default:
      return "OTHER";
  }
}

export function statusFilterToExpirationType(sf: StatusFilter): ExpirationType {
  if (sf === "soon") return "GOING_TO_EXPIRE";
  return "EXPIRED";
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
        id: `${dto.id}__${exp ?? "none"}`,
        name: displayName,
        quantity: it.quantity,
        location: mapLocationTolocation(dto.location),
        expiresAt: exp ?? undefined,
        productId: String(dto.id),
        expirationDate: exp,
        originalName: dto.original_name,
        hasNickname,
        status: it.status,
      };
    });
  }

  return [
    {
      id: `${dto.id}__none`,
      name: displayName,
      quantity: dto.quantity ?? 0,
      location: mapLocationTolocation(dto.location),
      expiresAt: undefined,
      productId: String(dto.id),
      expirationDate: null,
      originalName: dto.original_name,
      hasNickname,
    },
  ];
}

export function rowsSignature(rows: InventoryRow[]) {
  const sorted = [...rows].sort((a, b) => a.id.localeCompare(b.id));
  return sorted
    .map(
      (r) =>
        `${r.id}:${r.productId}:${r.quantity}:${r.expiresAt ?? ""}:${r.name}:${r.originalName}:${r.hasNickname ? 1 : 0}:${r.status ?? ""}`
    )
    .join("|");
}
