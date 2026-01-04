import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
} from "react";

export type Category = "fridge" | "freezer" | "pantry" | "cleaning supplies" | "other";


export type InventoryItem = {
  id: string;
  name: string;
  category: Category;
  quantity: number;
  expiresAt?: string;
};

type InventoryContextValue = {
  items: InventoryItem[];
  addItem: (item: Omit<InventoryItem, "id">) => void;
  updateItem: (id: string, patch: Partial<InventoryItem>) => void;
  removeItem: (id: string) => void;
  incrementQuantity: (id: string, delta?: number) => void;
  decrementQuantity: (id: string, delta?: number) => void;
};

const InventoryContext = createContext<InventoryContextValue | undefined>(
  undefined
);

export function InventoryProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<InventoryItem[]>([]);

  const addItem = (item: Omit<InventoryItem, "id">) => {
    const id = Date.now().toString();
    setItems((prev) => [...prev, { ...item, id }]);
  };

  const updateItem = (id: string, patch: Partial<InventoryItem>) => {
    setItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, ...patch } : it))
    );
  };

  const removeItem = (id: string) => {
    setItems((prev) => prev.filter((it) => it.id !== id));
  };

  const incrementQuantity = (id: string, delta = 1) => {
    setItems((prev) =>
      prev.map((it) =>
        it.id === id ? { ...it, quantity: it.quantity + delta } : it
      )
    );
  };

  const decrementQuantity = (id: string, delta = 1) => {
    setItems((prev) =>
      prev.map((it) =>
        it.id === id
          ? { ...it, quantity: Math.max(0, it.quantity - delta) }
          : it
      )
    );
  };

  return (
    <InventoryContext.Provider
      value={{
        items,
        addItem,
        updateItem,
        removeItem,
        incrementQuantity,
        decrementQuantity,
      }}
    >
      {children}
    </InventoryContext.Provider>
  );
}

export function useInventory() {
  const ctx = useContext(InventoryContext);
  if (!ctx) {
    throw new Error("useInventory must be used within InventoryProvider");
  }
  return ctx;
}
