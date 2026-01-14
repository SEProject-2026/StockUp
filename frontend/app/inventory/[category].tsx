import React from "react";
import { useLocalSearchParams } from "expo-router";
import { InventoryScreenBase } from "./inventory";
import type { location } from "@/src/context/inventory-context";

export default function InventorylocationScreen() {
  const { location } = useLocalSearchParams<{ location: string }>();

  return (
    <InventoryScreenBase
      initiallocation={location as location}
    />
  );
}
