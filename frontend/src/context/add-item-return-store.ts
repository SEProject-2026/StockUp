// src/context/add-item-return-store.ts

export type AddItemReturnDraft = {
  name: string;
  quantity: number;
  barcode?: string | null;
  nickname?: string | null;
  expiration_date?: string | null; // "YYYY-MM-DD"
  location: "fridge" | "freezer" | "pantry" | "cleaning" | "other";
};

let lastDrafts: AddItemReturnDraft[] = []; // ✅ לא null

export function setLastAddItemReturnDrafts(drafts: AddItemReturnDraft[]) {
  lastDrafts = drafts;
}

export function consumeLastAddItemReturnDrafts(): AddItemReturnDraft[] {
  const v = lastDrafts;
  lastDrafts = [];
  return v;
}
