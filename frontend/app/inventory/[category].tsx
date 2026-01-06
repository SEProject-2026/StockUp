import React from "react";
import { useLocalSearchParams } from "expo-router";
import { InventoryScreenBase } from "./inventory";
import type { Category } from "@/src/context/inventory-context";

export default function InventoryCategoryScreen() {
  const { category } = useLocalSearchParams<{ category: string }>();

  return (
    <InventoryScreenBase
      initialCategory={category as Category}
    />
  );
}
