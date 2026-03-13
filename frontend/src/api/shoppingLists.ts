import { authFetch } from "@/src/api/client";

export type GeneralResponse<T = unknown> = {
  status: "success" | "error";
  message?: string;
  data?: T;
};

export type LocationType =
  | "FRIDGE"
  | "FREEZER"
  | "PANTRY"
  | "CLEANING"
  | "BATHROOM"
  | "LAUNDRY"
  | "OTHER";

export type ShoppingListItemDTO = {
  item_name: string;
  quantity: number;
  is_bought: boolean;
  location: LocationType;
};

export type ShoppingListDTO = {
  id: string;
  home_id: string;
  name: string;
  is_active_shopping_mode: boolean;
  items: ShoppingListItemDTO[];
  updated_at: string;
};

export type CreateShoppingListRequest = {
  home_id: string;
  name: string;
};

export type AddItemRequest = {
  item_name: string;
  quantity: number;
  location?: LocationType;
};

export type UpdateQuantityRequest = {
  new_quantity: number;
};

export type ExitModeRequest = {
  clear?: boolean;
};

const BASE = "/shopping-lists";

function unwrapResponse<T>(response: GeneralResponse<T>): T {
  if (response.status !== "success") {
    throw new Error(response.message || "Request failed");
  }

  if (response.data === undefined) {
    throw new Error("Response data is missing");
  }

  return response.data;
}

export async function createShoppingList(
  payload: CreateShoppingListRequest
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(`${BASE}/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return unwrapResponse(response);
}

export async function getHomeShoppingLists(
  homeId: string
): Promise<ShoppingListDTO[]> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO[]>>(
    `${BASE}/home/${homeId}`,
    { method: "GET" }
  );

  return unwrapResponse(response);
}

export async function getShoppingList(
  listId: string
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(
    `${BASE}/${listId}`,
    { method: "GET" }
  );

  return unwrapResponse(response);
}

export async function addItemToShoppingList(
  listId: string,
  payload: AddItemRequest
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(
    `${BASE}/${listId}/items`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );

  return unwrapResponse(response);
}

export async function updateShoppingListItemQuantity(
  listId: string,
  itemName: string,
  newQuantity: number
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(
    `${BASE}/${listId}/items/${encodeURIComponent(itemName)}/quantity`,
    {
      method: "PATCH",
      body: JSON.stringify({ new_quantity: newQuantity }),
    }
  );

  return unwrapResponse(response);
}

export async function checkShoppingListItemAsBought(
  listId: string,
  itemName: string
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(
    `${BASE}/${listId}/items/${encodeURIComponent(itemName)}/check`,
    {
      method: "PATCH",
    }
  );

  return unwrapResponse(response);
}
export async function enterShoppingMode(
  listId: string
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(
    `${BASE}/${listId}/enter-mode`,
    {
      method: "POST",
    }
  );

  return unwrapResponse(response);
}

export async function exitShoppingMode(
  listId: string,
  payload: ExitModeRequest = { clear: false }
): Promise<ShoppingListDTO> {
  const response = await authFetch<GeneralResponse<ShoppingListDTO>>(
    `${BASE}/${listId}/exit-mode`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );

  return unwrapResponse(response);
}

export async function deleteShoppingList(listId: string): Promise<void> {
  await authFetch<void>(`${BASE}/${listId}`, {
    method: "DELETE",
  });
}