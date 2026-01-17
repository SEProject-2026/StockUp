// src/context/add-item-return-store.ts
import type { location } from "@/src/components/add-item/types";
import type { UnitType } from "@/src/components/receipts/review/review.shared";

export type AddItemReturnDraft = {
  name: string;
  quantity: number;
  barcode?: string | null;
  nickname?: string | null;
  expiration_date?: string | null; // "YYYY-MM-DD" | null
  location: location; 
  unit?: UnitType;
};

let lastDrafts: AddItemReturnDraft[] | null = null;

export function setLastAddItemReturnDrafts(drafts: AddItemReturnDraft[]) {
  lastDrafts = drafts;
}

export function consumeLastAddItemReturnDrafts(): AddItemReturnDraft[] | null {
  const out = lastDrafts;
  lastDrafts = null;
  return out;
}
