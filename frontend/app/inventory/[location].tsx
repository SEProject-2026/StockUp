import React from "react";
import { useLocalSearchParams } from "expo-router";
import { InventoryScreenBase } from "./inventory";
import type { location as Location } from "@/src/context/inventory-context";

export default function InventoryLocationScreen() {
  const params = useLocalSearchParams<{ location?: string; homeId?: string }>();
  const locParam = Array.isArray(params.location) ? params.location[0] : params.location;

  const initialLocation = (locParam ?? "other") as Location;

  return <InventoryScreenBase initiallocation={initialLocation} />;
}
